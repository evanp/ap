
import { parseArgs } from "node:util"
import { LoginCommand } from "./commands/login.mjs"
import { CreateNoteCommand } from "./commands/create-note.mjs"

process.env.NODE_TLS_REJECT_UNAUTHORIZED = 0

async function main(argv) {
  const args = parseArgs({args: argv, strict: false, allowPositionals: true})

  if (args.positionals.length === 0) {
    throw new Error("No command provided")
  }

  let command = null

  switch (args.positionals[0]) {
    case "login":
      command = new LoginCommand(args)
      break
    case "create":
      if (args.positionals.length < 2) {
        throw new Error('No type provided for create')
      }
      switch (args.positionals[1]) {
        case "note":
          command = new CreateNoteCommand(args)
          break
        default:
          throw new Error(`Unknown content type: ${args.positionals[1]}`)
      }
      break
    default:
      throw new Error(`Unknown command: ${args.positionals[0]}`)
  }

  await command.run()
}

main(process.argv.slice(2))
.then(() => process.exit(0))
.catch(err => {
    console.error(err)
    process.exit(1)
})
