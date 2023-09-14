import { describe, it } from 'node:test'
import { parseArgs } from 'node:util'
import { CreateNoteCommand } from '../commands/create-note.mjs'
import assert from 'node:assert'
import { Command } from '../command.mjs'

process.env.NODE_TLS_REJECT_UNAUTHORIZED = 0

describe('Create Note command', async () => {

  const text = 'now is the time for all good people'

  it('can execute the command', async () => {
    const args = parseArgs({args: [text], allowPositionals: true})
    const command = new CreateNoteCommand(args)
    command.run()
  })

  it('can find the activity in the inbox', async() => {
    const actor = await Command.getActor()
    const items = await Command.getCollectionItems(actor.inbox.id)
    const activity = items.find(item => item.type === 'Create' && item.object.type === 'Note' && item.object.contentMap.en === text)
    assert.ok(activity)
  })

  it('can find the activity in the outbox', async () => {
    const actor = await Command.getActor()
    const items = await Command.getCollectionItems(actor.outbox.id)
    const activity = items.find(item => item.type === 'Create' && item.object.type === 'Note' && item.object.contentMap.en === text)
    assert.ok(activity)
  })
})
