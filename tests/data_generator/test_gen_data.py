import pytest
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

# Add current directory to path to allow importing generate_test_data
# This is necessary because generate_test_data.py is a script in the same directory, not a module in a package in standard sense
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import generate_test_data

class TestGenerateTestData:
    def test_generate_discipleship_string(self):
        """Test that discipleship strings are generated correctly based on prerequisites."""
        ds = generate_test_data.generate_discipleship_string()
        assert isinstance(ds, str)
        if "Leadership L113" in ds:
            assert "One2One" in ds
            
    def test_generate_base_profile(self):
        """Test profile generation with and without overrides."""
        profile = generate_test_data.generate_base_profile()
        assert "firstName" in profile
        assert "email" in profile
        
        overrides = {
            "firstName": "TestFirst",
            "lastName": "TestLast",
            "occupationType": "Student"
        }
        profile_override = generate_test_data.generate_base_profile(overrides)
        assert profile_override["firstName"] == "TestFirst"
        assert profile_override["lastName"] == "TestLast"
        assert profile_override["occupationType"] == "Student"

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_execution(self, mock_json_dump, mock_file):
        """Test the main function runs and attempts to write JSON."""
        generate_test_data.main()
        mock_file.assert_called_with('test_cases.json', 'w')
        assert mock_json_dump.called
        args, _ = mock_json_dump.call_args
        data = args[0]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_ministry_logic_consistency(self):
        """Test that ministry logic respects overrides."""
        p1 = generate_test_data.generate_base_profile({"isMinistryMember": "Yes", "ministry": "Worship"})
        assert p1["isMinistryMember"] == "Yes"
        assert p1["ministry"] == "Worship"
        
        p2 = generate_test_data.generate_base_profile({"isMinistryMember": "No"})
        assert p2["isMinistryMember"] == "No"
        assert p2["ministry"] == "None" 
