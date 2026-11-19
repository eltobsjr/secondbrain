"""install-tools.sh e a conferência `--check` (P1-3), num HOME isolado."""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL = os.path.join(HERE, "..", "scripts", "install-tools.sh")


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="install-")
        self.env = dict(os.environ, HOME=self.home)
        self.sb = os.path.join(self.home, ".local/share/secondbrain/bin")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def run_(self, *args):
        return subprocess.run(["bash", INSTALL, *args], env=self.env, capture_output=True, text=True, timeout=60)

    def test_check_acusa_falta_instala_e_acusa_defasagem(self):
        r = self.run_("--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("falta:", r.stdout)
        self.assertEqual(self.run_().returncode, 0)
        self.assertEqual(self.run_("--check").returncode, 0, self.run_("--check").stdout)
        with open(os.path.join(self.sb, "xmem.py"), "a") as fh:
            fh.write("\n# versão antiga\n")
        r = self.run_("--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("defasado:   xmem.py", r.stdout)

    def test_instalar_grava_a_versao(self):
        self.run_()
        self.assertTrue(open(os.path.join(self.sb, "VERSION")).read().strip())


if __name__ == "__main__":
    unittest.main()
