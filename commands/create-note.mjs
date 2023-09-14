import { Command } from '../command.mjs'

export class CreateNoteCommand extends Command {
  constructor(args) {
    super(args)
    this.content = args.positionals?.join(' ')
  }
  async run() {
    const activity = await this.postActivity({
      type: 'Create',
      to: 'Public',
      object: {
        type: 'Note',
        contentMap: {
          en: this.content
        }
      }
    })
    if (activity) {
      console.log(`Created note ${activity.object.id} (activity id ${activity.id})`)
    }
  }
}