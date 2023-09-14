import { join } from 'node:path'
import { readFileSync } from 'node:fs'

export class Command {
  constructor(args) {
      this.args = args
  }

  async run() {
      throw new Error("run() not implemented")
  }

  static async fetchActorId(webfinger) {
    const parts = webfinger.split("@", 2)
    const domain = parts[1]
    const url = `https://${domain}/.well-known/webfinger?resource=acct:${webfinger}`
    const res = await fetch(url, {
      headers: {
        accept: "application/jrd+json,application/json"
      }
    })
    if (res.status !== 200) {
      throw new Error(`Error fetching webfinger: ${res.status}`)
    }
    const jrd = await res.json()
    const link = jrd.links.find((link) => link.rel === "self" && link.type === "application/activity+json")
    if (!link) {
      throw new Error(`No self link found in webfinger response`)
    }
    return link.href
  }

  static async fetchActor(actorId) {
    const res = await fetch(actorId, {
      headers: {
        accept: "application/ld+json,application/activity+json,application/json"
      }
    })
    if (res.status !== 200) {
      throw new Error(`Error fetching actor: ${res.status}`)
    }
    return await res.json()
  }

  static async getAccessToken() {
    const filename = join(process.env.HOME, '.ap-token')
    const values = JSON.parse(readFileSync(join(process.env.HOME, '.ap-token')))
    // TODO: check if expired
    return values.access_token
  }

  static async getActorId() {
    const filename = join(process.env.HOME, '.ap-token')
    const values = JSON.parse(readFileSync(join(process.env.HOME, '.ap-token')))
    // TODO: check if expired
    return values.actorId
  }

  static async getActor() {
    const actorId = await Command.getActorId()
    return await Command.fetchActor(actorId)
  }

  static async getObject(objectId) {
    const token = await Command.getAccessToken()
    const res = await fetch(objectId, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/ld+json,application/activity+json,application/json'
      }
    })
    if (res.status !== 200) {
      throw new Error(`Bad status getting ${objectId}: ${res.status}`)
    }
    return await res.json()
  }

  static async getCollectionItems(collectionId) {
    const coll = await Command.getObject(collectionId)
    if (coll.items) {
      return coll.items
    } else if (coll.orderedItems) {
    } else if (coll.first && coll.first.id) {
      const first = await Command.getObject(coll.first.id)
      if (first.items) {
        return first.items
      } else if (first.orderedItems) {
        return first.orderedItems
      } else {
        throw new Error(`No items in first page`)
      }
    } else {
      throw new Error(`Don't know how to get items from ${collectionId}`)
    }
  }

  async postActivity(json) {
    const token = await Command.getAccessToken()
    const actor = await Command.getActor()
    const res = await fetch(actor.outbox.id, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
      },
      body: JSON.stringify(json)
    })
    if (res.status !== 201) {
      throw new Error(`Incorrect status: ${res.status}`)
    }
    return await res.json()
  }
}