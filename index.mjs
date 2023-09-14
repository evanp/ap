
import { parseArgs } from "node:util"
import { LoginCommand } from "./commands/login.mjs"

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
