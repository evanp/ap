
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
}