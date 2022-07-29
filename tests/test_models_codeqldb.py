import sys
import unittest
sys.path.append(".")

from codeqlsummarize.models import CodeQLDatabase


class TestModelCodeQLDB(unittest.TestCase):
    def test_display_name(self):
        db = CodeQLDatabase("repo", "java", "./", repository="test/repo") 
        self.assertEqual(db.display_name(), "TestRepo")

        db = CodeQLDatabase("repo", "java", "./", repository="test/repo-name") 
        self.assertEqual(db.display_name(), "TestRepoName")

        db = CodeQLDatabase("repo", "java", "./", repository="test-org/name") 
        self.assertEqual(db.display_name(), "TestOrgName")

        db = CodeQLDatabase("repo", "java", "./", repository="test-org/repo-name") 
        self.assertEqual(db.display_name(), "TestOrgRepoName")

        db = CodeQLDatabase("repo", "java", "./", repository=None) 
        self.assertEqual(db.display_name(), "Repo")

        
        db = CodeQLDatabase("repo", "java", "./", repository="test/repo") 
        self.assertEqual(db.display_name(owner="test"), "Repo")

        db = CodeQLDatabase("repo", "java", "./", repository="test/repo-name") 
        self.assertEqual(db.display_name(owner="test"), "RepoName")

