import { describe, it } from 'node:test'
import { parseArgs } from 'node:util'
import { join } from 'node:path'
import { readFileSync } from 'node:fs'
import { LoginCommand } from '../commands/login.mjs'
import assert from 'node:assert'
import { Command } from '../command.mjs'

process.env.NODE_TLS_REJECT_UNAUTHORIZED = 0

describe('Login command', async () => {

  it('Login by webfinger', async() => {
    const webfinger = 'evanp@localhost:3000'
    const argv = ['login', webfinger]
    const args = parseArgs({args: argv, allowPositionals: true})
    const command = new LoginCommand(args)
    await command.run()
    const tokens = JSON.parse(readFileSync(join(process.env.HOME, '.ap-token')))
    const actorId = await Command.fetchActorId(webfinger)
    assert.ok(tokens.access_token)
    assert.ok(tokens.refresh_token)
    assert.strictEqual(tokens.actorId, actorId)
    assert.ok(tokens.loginAt)
  })

  it('Login by actor ID', async () => {
    const webfinger = 'evanp@localhost:3000'
    const actorId = await Command.fetchActorId(webfinger)
    const argv = ['login', actorId]
    const args = parseArgs({args: argv, allowPositionals: true})
    const command = new LoginCommand(args)
    await command.run()
    const tokens = JSON.parse(readFileSync(join(process.env.HOME, '.ap-token')))
    assert.ok(tokens.access_token)
    assert.ok(tokens.refresh_token)
    assert.strictEqual(tokens.actorId, actorId)
    assert.ok(tokens.loginAt)
  })
})
