#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests the GRR hunt collectors."""

import unittest
import zipfile
import mock

from grr_response_proto import flows_pb2
from grr_response_proto import osquery_pb2 as osquery_flows

from dftimewolf import config
from dftimewolf.lib import state
from dftimewolf.lib import errors
from dftimewolf.lib.collectors import grr_hunt
from dftimewolf.lib.containers import containers
from tests.lib.collectors.test_data import mock_grr_hosts


# Mocking of classes.
# pylint: disable=invalid-name,arguments-differ
class GRRHuntArtifactCollectorTest(unittest.TestCase):
  """Tests for the GRR artifact collector."""

  # For pytype
  grr_hunt_artifact_collector: grr_hunt.GRRHuntArtifactCollector
  mock_grr_api: mock.Mock

  @mock.patch('grr_api_client.api.InitHttp')
  def setUp(self, mock_InitHttp):
    self.mock_grr_api = mock.Mock()
    mock_InitHttp.return_value = self.mock_grr_api
    self.test_state = state.DFTimewolfState(config.Config)
    self.grr_hunt_artifact_collector = grr_hunt.GRRHuntArtifactCollector(
        self.test_state)
    self.grr_hunt_artifact_collector.SetUp(
        artifacts='RandomArtifact',
        use_tsk=True,
        reason='random reason',
        grr_server_url='http://fake/endpoint',
        grr_username='admin',
        grr_password='admin',
        approvers='approver1,approver2',
        max_file_size='1234',
        verify=False,
        match_mode=None,
        client_operating_systems=None,
        client_labels=None
    )

  def testProcess(self):
    """Tests that the process function issues correct GRR API calls."""
    self.grr_hunt_artifact_collector.Process()
    # extract call kwargs
    call_kwargs = self.mock_grr_api.CreateHunt.call_args[1]
    self.assertEqual(call_kwargs['flow_args'].artifact_list,
                     ['RandomArtifact'])
    self.assertEqual(call_kwargs['flow_args'].use_tsk, True)
    self.assertEqual(call_kwargs['flow_name'], 'ArtifactCollectorFlow')
    self.assertEqual(call_kwargs['hunt_runner_args'].description,
                     'random reason')


class GRRHuntFileCollectorTest(unittest.TestCase):
  """Tests for the GRR file collector."""

  # For pytype
  grr_hunt_file_collector: grr_hunt.GRRHuntFileCollector
  mock_grr_api: mock.Mock

  @mock.patch('grr_api_client.api.InitHttp')
  def setUp(self, mock_InitHttp):
    self.mock_grr_api = mock.Mock()
    mock_InitHttp.return_value = self.mock_grr_api
    self.test_state = state.DFTimewolfState(config.Config)
    self.test_state.StoreContainer(containers.FSPath(path='/etc/hosts'))
    self.grr_hunt_file_collector = grr_hunt.GRRHuntFileCollector(
        self.test_state)
    self.grr_hunt_file_collector.SetUp(
        file_path_list='/etc/passwd,/etc/shadow',
        reason='random reason',
        grr_server_url='http://fake/endpoint',
        grr_username='admin',
        grr_password='admin',
        approvers='approver1,approver2',
        max_file_size='1234',
        verify=False,
        match_mode=None,
        client_operating_systems=None,
        client_labels=None
    )

  def testInitialization(self):
    """Tests that the collector can be initialized."""
    self.assertEqual(
        self.grr_hunt_file_collector.file_path_list,
        ['/etc/passwd', '/etc/shadow']
    )

  def testPreProcess(self):
    """Tests the preprocess method."""
    self.grr_hunt_file_collector.PreProcess()
    self.assertEqual(
        self.grr_hunt_file_collector.file_path_list,
        ['/etc/passwd', '/etc/shadow', '/etc/hosts'])

  def testProcess(self):
    """Tests that the process method invokes the correct GRR API calls."""
    self.grr_hunt_file_collector.PreProcess()
    self.grr_hunt_file_collector.Process()
    # extract call kwargs
    call_kwargs = self.mock_grr_api.CreateHunt.call_args[1]
    self.assertEqual(call_kwargs['flow_args'].paths,
                     ['/etc/passwd', '/etc/shadow', '/etc/hosts'])
    self.assertEqual(call_kwargs['flow_args'].action.action_type,
                     flows_pb2.FileFinderAction.DOWNLOAD)
    self.assertEqual(call_kwargs['flow_name'], 'FileFinder')
    self.assertEqual(call_kwargs['hunt_runner_args'].description,
                     'random reason')


class GRRHuntOsqueryCollectorTest(unittest.TestCase):
  """Tests for the GRR osquery collector."""

  # For pytype
  grr_hunt_osquery_collector: grr_hunt.GRRHuntOsqueryCollector
  mock_grr_api: mock.Mock

  @mock.patch('grr_api_client.api.InitHttp')
  def setUp(self, mock_InitHttp):
    self.mock_grr_api = mock.Mock()
    mock_InitHttp.return_value = self.mock_grr_api
    self.test_state = state.DFTimewolfState(config.Config)
    self.test_state.StoreContainer(
        containers.OsqueryQuery(query='SELECT * FROM processes'))
    self.grr_hunt_osquery_collector = grr_hunt.GRRHuntOsqueryCollector(
        self.test_state)
    self.grr_hunt_osquery_collector.SetUp(
        reason='random reason',
        timeout_millis=300000,
        ignore_stderr_errors=False,
        grr_server_url='http://fake/endpoint',
        grr_username='admin',
        grr_password='admin',
        approvers='approver1,approver2',
        verify=False,
        match_mode=None,
        client_operating_systems=None,
        client_labels=None)

  def testProcess(self):
    """Tests that the process method invokes the correct GRR API calls."""
    self.grr_hunt_osquery_collector.Process()
    # extract call kwargs
    call_kwargs = self.mock_grr_api.CreateHunt.call_args[1]
    self.assertEqual(call_kwargs['flow_args'].query,
                     'SELECT * FROM processes')
    self.assertEqual(call_kwargs['flow_args'].timeout_millis,
                     300000)
    self.assertEqual(call_kwargs['flow_args'].ignore_stderr_errors, False)
    self.assertEqual(call_kwargs['flow_name'], 'OsqueryFlow')
    self.assertEqual(call_kwargs['hunt_runner_args'].description,
                     'random reason')

class GRRHuntDownloader(unittest.TestCase):
  """Tests for the GRR hunt downloader."""

  # For pytype
  grr_hunt_downloader: grr_hunt.GRRHuntDownloader
  mock_grr_api: mock.Mock

  @mock.patch('grr_api_client.api.InitHttp')
  def setUp(self, mock_InitHttp):
    self.mock_grr_api = mock.Mock()
    mock_InitHttp.return_value = self.mock_grr_api
    self.test_state = state.DFTimewolfState(config.Config)
    self.grr_hunt_downloader = grr_hunt.GRRHuntDownloader(self.test_state)
    self.grr_hunt_downloader.SetUp(
        hunt_id='H:12345',
        reason='random reason',
        grr_server_url='http://fake/endpoint',
        grr_username='admin',
        grr_password='admin',
        approvers='approver1,approver2',
        verify=False
    )
    self.grr_hunt_downloader.output_path = '/tmp/test'

  def testInitialization(self):
    """Tests that the collector is correctly initialized."""
    self.assertEqual(self.grr_hunt_downloader.hunt_id, 'H:12345')

  @mock.patch('dftimewolf.lib.collectors.grr_hunt.GRRHuntDownloader._ExtractHuntResults')  # pylint: disable=line-too-long
  @mock.patch('dftimewolf.lib.collectors.grr_hunt.GRRHuntDownloader._GetAndWriteArchive')  # pylint: disable=line-too-long
  def testCollectHuntResults(self,
                             mock_get_write_archive,
                             mock_ExtractHuntResults):
    """Tests that hunt results are downloaded to the correct file."""
    self.mock_grr_api.Hunt.return_value.Get.return_value = \
        mock_grr_hosts.MOCK_HUNT
    self.grr_hunt_downloader.Process()
    mock_get_write_archive.assert_called_with(mock_grr_hosts.MOCK_HUNT,
                                              '/tmp/test/H:12345.zip')
    mock_ExtractHuntResults.assert_called_with('/tmp/test/H:12345.zip')

  @mock.patch('os.remove')
  @mock.patch('zipfile.ZipFile.extract')
  def testExtractHuntResults(self, _, mock_remove):
    """Tests that hunt results are correctly extracted."""
    self.grr_hunt_downloader.output_path = '/directory'
    expected = sorted([
        ('greendale-student04.c.greendale.internal',
         '/directory/hunt_H_A43ABF9D/C.4c4223a2ea9cf6f1'),
        ('greendale-admin.c.greendale.internal',
         '/directory/hunt_H_A43ABF9D/C.ba6b63df5d330589'),
        ('greendale-student05.c.greendale.internal',
         '/directory/hunt_H_A43ABF9D/C.fc693a148af801d5')
    ])
    test_zip = 'tests/lib/collectors/test_data/hunt.zip'
    # pylint: disable=protected-access
    result = sorted(self.grr_hunt_downloader._ExtractHuntResults(test_zip))
    self.assertEqual(result, expected)
    mock_remove.assert_called_with('tests/lib/collectors/test_data/hunt.zip')

  @mock.patch('os.remove')
  @mock.patch('zipfile.ZipFile.extract')
  def testOSErrorExtractHuntResults(self, mock_extract, mock_remove):
    """Tests that an OSError when reading files generate errors."""
    self.grr_hunt_downloader.output_path = '/directory'
    test_zip = 'tests/lib/collectors/test_data/hunt.zip'
    mock_extract.side_effect = OSError
    # pylint: disable=protected-access

    with self.assertRaises(errors.DFTimewolfError) as error:
      self.grr_hunt_downloader._ExtractHuntResults(test_zip)
    self.assertEqual(1, len(self.test_state.errors))
    self.assertEqual(
        error.exception.message,
        'Error manipulating file tests/lib/collectors/test_data/hunt.zip: ')
    self.assertTrue(error.exception.critical)
    mock_remove.assert_not_called()

  @mock.patch('os.remove')
  @mock.patch('zipfile.ZipFile.extract')
  def testBadZipFileExtractHuntResults(self, mock_extract, mock_remove):
    """Tests that a BadZipFile error when reading files generate errors."""
    self.grr_hunt_downloader.output_path = '/directory'
    test_zip = 'tests/lib/collectors/test_data/hunt.zip'

    mock_extract.side_effect = zipfile.BadZipfile
    # pylint: disable=protected-access
    with self.assertRaises(errors.DFTimewolfError) as error:
      self.grr_hunt_downloader._ExtractHuntResults(test_zip)

    self.assertEqual(1, len(self.test_state.errors))
    self.assertEqual(
        error.exception.message,
        'Bad zipfile tests/lib/collectors/test_data/hunt.zip: ')
    self.assertTrue(error.exception.critical)
    mock_remove.assert_not_called()


class GRRHuntOsqueryDownloader(unittest.TestCase):
  """Tests for the GRR Osquery hunt downloader."""

  @mock.patch('grr_api_client.api.InitHttp')
  def setUp(self, mock_InitHttp):
    self.mock_grr_api = mock.Mock()
    mock_InitHttp.return_value = self.mock_grr_api
    self.test_state = state.DFTimewolfState(config.Config)
    self.grr_hunt_downloader = grr_hunt.GRRHuntOsqueryDownloader(
        self.test_state)
    self.grr_hunt_downloader.SetUp(
        hunt_id='H:12345',
        reason='random reason',
        grr_server_url='http://fake/endpoint',
        grr_username='admin',
        grr_password='admin',
        approvers='approver1,approver2',
        verify=False
    )
    self.grr_hunt_downloader.output_path = '/tmp/test'

  def testInitialization(self):
    """Tests that the collector is correctly initialized."""
    # pytype: disable=attribute-error
    self.assertEqual(self.grr_hunt_downloader.hunt_id, 'H:12345')
    # pytype: enable=attribute-error

  @mock.patch('dftimewolf.lib.collectors.grr_hunt.GRRHuntOsqueryDownloader._GetAndWriteResults')  # pylint: disable=line-too-long
  def testProcess(self, mock_get_write_results):
    """Tests that hunt results are downloaded to the correct path."""
    self.mock_grr_api.Hunt.return_value.Get.return_value = \
        mock_grr_hosts.MOCK_HUNT
    self.grr_hunt_downloader.Process()
    mock_get_write_results.assert_called_with(mock_grr_hosts.MOCK_HUNT,
                                              '/tmp/test')

  @mock.patch('grr_api_client.hunt.Hunt.ListResults')
  def testGetAndWriteResults(self, mock_list_results):
    """Tests the GetAndWriteReslts function."""
    mock_result = mock.MagicMock()
    mock_result.payload = mock.MagicMock(spec=osquery_flows.OsqueryResult)
    mock_list_results.return_value = [mock_result]
    mock_client = mock.MagicMock()
    mock_client.data.os_info.fqdn = 'TEST'
    self.mock_grr_api.SearchClients.return_value = [mock_client]

    results = self.grr_hunt_downloader._GetAndWriteResults(  # pylint: disable=protected-access
        mock_grr_hosts.MOCK_HUNT, '/tmp/test')

    self.assertEqual(len(results), 1)
    self.assertEqual(results[0][0], 'test')
    self.assertEqual(results[0][1], '/tmp/test/test.csv')

  @mock.patch('grr_api_client.hunt.Hunt.ListResults')
  def testGetAndWriteWrongResults(self, mock_list_results):
    """Tests the GetAndWriteReslts function with wrong results."""
    mock_result = mock.MagicMock()
    mock_result.payload = mock.MagicMock(spec=flows_pb2.FileFinderResult)
    mock_list_results.return_value = [mock_result]
    mock_client = mock.MagicMock()
    mock_client.data.os_info.fqdn = 'TEST'
    self.mock_grr_api.SearchClients.return_value = [mock_client]

    # pylint: disable=protected-access
    with self.assertRaises(errors.DFTimewolfError) as error:
      self.grr_hunt_downloader._GetAndWriteResults(
          mock_grr_hosts.MOCK_HUNT, '/tmp/test')

    self.assertEqual(1, len(self.test_state.errors))
    self.assertIn('Incorrect results format from', error.exception.message)
    self.assertIn('Possibly not an osquery hunt.', error.exception.message)
    self.assertTrue(error.exception.critical)


if __name__ == '__main__':
  unittest.main()
