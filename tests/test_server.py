import asyncio
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ubuntu_mcp_server.server import SecurityChecker, SecurityViolation, create_secure_policy


class CommandPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = create_secure_policy()
        self.checker = SecurityChecker(self.policy)

    def test_sudo_disabled_including_absolute_path(self):
        for command in ('sudo whoami', '/usr/bin/sudo whoami'):
            with self.subTest(command=command), self.assertRaises(SecurityViolation):
                self.checker.validate_command(command)

    def test_sudo_allow_list_and_noninteractive_argv(self):
        self.policy.allow_sudo = True
        self.policy.sudo_commands = ['/usr/bin/whoami']
        for command in ('sudo whoami', 'sudo -n whoami', '/usr/bin/sudo -- whoami'):
            argv = self.checker.validate_command(command)
            self.assertEqual(argv[1:], ['-n', '--', str(Path('/usr/bin/whoami').resolve())])

    def test_sudo_rejects_options_and_unapproved_commands(self):
        self.policy.allow_sudo = True
        self.policy.sudo_commands = ['/usr/bin/whoami']
        for command in ('sudo', 'sudo -S whoami', 'sudo -u root whoami', 'sudo cat /etc/shadow', 'sudo sudo whoami'):
            with self.subTest(command=command), self.assertRaises(SecurityViolation):
                self.checker.validate_command(command)

    def test_command_resolution_ignores_inherited_path(self):
        with patch.dict(os.environ, {'PATH': '/nonexistent'}):
            self.assertEqual(self.checker.validate_command('echo hello'), ['/usr/bin/echo', 'hello'])

    def test_shell_mode_rejected(self):
        self.policy.use_shell_exec = True
        with self.assertRaises(SecurityViolation):
            self.checker.validate_command('echo hi')


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_handshake_discovery_and_calls(self):
        await asyncio.wait_for(self.check_protocol(), timeout=20)

    async def check_protocol(self):
        params = StdioServerParameters(command=sys.executable, args=['-m', 'ubuntu_mcp_server'])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                self.assertTrue(initialized.server_info.name)
                names = {tool.name for tool in (await session.list_tools()).tools}
                self.assertEqual(names, {'execute_command', 'list_directory', 'read_file', 'write_file', 'get_system_info', 'install_package', 'search_packages'})
                result = await session.call_tool('execute_command', {'command': 'echo codex-compatible'})
                data = json.loads(result.content[0].text)
                self.assertEqual(data['stdout'], 'codex-compatible\n')
                self.assertEqual(data['return_code'], 0)
                result = await session.call_tool('execute_command', {'command': 'sudo whoami'})
                self.assertEqual(json.loads(result.content[0].text)['type'], 'SecurityViolation')
                result = await session.call_tool('execute_command', {'command': 'echo hello; whoami'})
                self.assertEqual(json.loads(result.content[0].text)['stdout'], 'hello; whoami\n')


if __name__ == '__main__':
    unittest.main()
