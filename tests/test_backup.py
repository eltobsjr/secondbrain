"""backup.sh com ponto de montagem que tem espaço no nome (P1-3). Usa uma pasta comum no lugar do HD e um HOME isolado."""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "backup.sh")


@unittest.skipUnless(shutil.which("rsync") and shutil.which("bash"), "precisa de rsync e bash")
class BackupTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="backup-")
        self.home = os.path.join(self.base, "home")
        self.hd = os.path.join(self.base, "HD externo")          # espaço no nome
        os.makedirs(self.hd)
        v = os.path.join(self.home, "dev/proj_a/ASecondBrain")
        os.makedirs(v)
        with open(os.path.join(v, "_secondbrain.md"), "w") as fh:
            fh.write("---\nschema: 2\n---\n")
        with open(os.path.join(v, "ESTADO.md"), "w") as fh:
            fh.write("# Estado\n")
        self.env = dict(os.environ, HOME=self.home, XDG_STATE_HOME=os.path.join(self.home, ".state"), SECONDBRAIN_TEST_DRIVE=self.hd)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def sb(self, *args):
        return subprocess.run(["bash", SCRIPT, *args], env=self.env, capture_output=True, text=True, timeout=60)

    def test_copia_para_hd_com_espaco_no_nome(self):
        self.assertEqual(self.sb("init", self.hd).returncode, 0)
        r = self.sb("run", "--force")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        host = subprocess.run(["hostname", "-s"], capture_output=True, text=True).stdout.strip()
        copiado = os.path.join(self.hd, "secondbrain-backup", host, "current", "dev/proj_a/ASecondBrain/ESTADO.md")
        self.assertTrue(os.path.isfile(copiado), "o ESTADO.md foi copiado para o HD com espaço no nome")

    def test_status_mostra_o_hd_com_espaco(self):
        self.sb("init", self.hd)
        r = self.sb("status")
        self.assertIn("HD externo", r.stdout)
        self.assertIn("último em", r.stdout)


if __name__ == "__main__":
    unittest.main()
