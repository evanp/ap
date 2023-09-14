import { Command } from '../command.mjs'
import open from 'open'
import querystring from 'querystring'
import { join } from 'node:path'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { randomBytes, createHash } from 'node:crypto'
import http from 'node:http'

const base64URLEncode = (str) =>
  str.toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')

export class LoginCommand extends Command {
  constructor(args) {
    if (args.positionals.length !== 2) {
      throw new Error("Expected exactly 2 positional arguments")
    }
    super(args)
    const id = args.positionals[1]
    if (id.match(/^https?:\/\//)) {
      this.actorId = id
    } else if (id.match(/@/)) {
      this.webfinger = id
    } else {
      throw new Error(`Unrecognized actor id: ${id}`)
    }
  }

  async run() {
    if (this.webfinger) {
      this.actorId = await Command.fetchActorId(this.webfinger)
    }
    this.actor = await Command.fetchActor(this.actorId)
    if (!this.actor) {
      throw new Error(`Unable to fetch actor: ${this.actorId}`)
    }
    const authz = this.actor.endpoints?.oauthAuthorizationEndpoint
    const tokenUrl = this.actor.endpoints?.oauthTokenEndpoint
    if (!authz) {
      throw new Error(`No authorization endpoint found for actor: ${this.actorId}`)
    }
    if (!tokenUrl) {
      throw new Error(`No token endpoint found for actor: ${this.actorId}`)
    }
    const state = Math.random().toString(36).substring(2)
    const clientId = "https://evanp.github.io/ap/client.jsonld"
    const redirectUri = "http://localhost:36696/callback"
    const scope = "read write"
    const codeVerifier = randomBytes(32).toString('hex')
    const codeChallenge = base64URLEncode(createHash('sha256').update(codeVerifier).digest())
    const qs = querystring.stringify({
      response_type: 'code',
      client_id: clientId,
      redirect_uri: redirectUri,
      scope,
      state,
      code_challenge_method: 'S256',
      code_challenge: codeChallenge
    })
    const url = `${authz}?${qs}`
    return new Promise((resolve, reject) => {
      const server = http.createServer((req, res) => {
        if (req.url.startsWith("/callback")) {
          const qs = querystring.parse(req.url.split("?")[1])
          if (qs.state !== state) {
            res.writeHead(400, { 'Content-Type': 'text/plain' });
            res.end('State mismatch');
            reject(new Error("State mismatch"))
          } else {
            const code = qs.code
            this.fetchToken(tokenUrl, code, codeVerifier, clientId, redirectUri)
            .then((results) => {
              this.writeToken(results)
              res.writeHead(200, { 'Content-Type': 'text/plain' });
              res.end('Success. You can close this window.');
              server.close()
              console.log("Login successful")
              resolve()
            })
            .catch((err) => {
              res.writeHead(400, { 'Content-Type': 'text/plain' });
              res.end('Error: ' + err.message);
              server.close()
              reject(err)
            })
          }
        } else {
          res.writeHead(400, { 'Content-Type': 'text/plain' });
          res.end('Bad Request');
        }
      })
      server.listen(36696)
      console.log(`Authorize the app by visiting: ${url}`)
      open(url)
    })
  }

  async fetchToken(tokenUrl, code, codeVerifier, clientId, redirectUri) {
    const res = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: querystring.stringify({
        grant_type: 'authorization_code',
        code,
        redirect_uri: redirectUri,
        code_verifier: codeVerifier,
        client_id: clientId
      })
    })
    if (res.status !== 200) {
      throw new Error(`Bad response from token endpoint ${res.status}`)
    }
    return await res.json()
  }

  async writeToken(results) {
    const filename = join(process.env.HOME, '.ap-token')
    results = {actorId: this.actorId, loginAt: Date.now()/1000, ...results}
    writeFileSync(filename, JSON.stringify(results))
  }
}