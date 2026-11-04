# Contributing to seekport

Thanks for taking the time to help. This project is small on purpose, so the
rules are short.

## Ways to help

- **Bug reports**: open an [issue](https://github.com/ChemistryBus/seekport/issues/new/choose)
  with the bug template. Include the command, the error, Python version, and
  which harness you use. **Never paste your API key.**
- **Feature requests**: open an issue with the feature template. Explain the
  problem first, then the proposed solution.
- **Pull requests**: welcome for bug fixes, tests, documentation, and small
  improvements. For larger changes, open an issue first so we can agree on the
  shape.

## Development

Requirements: Python 3.9+. There is nothing to install.

```bash
git clone https://github.com/ChemistryBus/seekport.git
cd seekport
python3 -m unittest discover -s tests -v
```

The suite mocks all HTTP, so it spends no API credits and needs no key.

## Pull request checklist

- [ ] `python3 -m unittest discover -s tests` passes.
- [ ] No new third-party runtime dependency. The core uses the standard library only.
- [ ] `scripts/ds_core.py` stays under 300 lines.
- [ ] Behaviour changes come with a test.
- [ ] User-facing changes update `README.md`, `README.zh-CN.md`, and `SKILL.md`.
- [ ] No secrets, keys, private URLs, or personal data in the diff.

## Style

- Small functions, clear names, no deep nesting.
- Prefer immutable data and explicit validation.
- Error messages should be safe to show to a user or an agent.
- Keep the CLI output stable: JSON is the machine contract, Markdown is for reading.

## Security

Do not open a public issue for a vulnerability, and never post a working API
key. If you find a security problem, describe it to the maintainer privately
first, then we can coordinate a fix and a disclosure.

## License

By contributing, you agree that your contribution is licensed under the MIT
License, the same as the project.
