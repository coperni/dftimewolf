#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests the Threaded Timesketch exporter."""

import unittest

import mock

from dftimewolf import config
from dftimewolf.lib import state
from dftimewolf.lib.containers import containers
from dftimewolf.lib.exporters import timesketch
from dftimewolf.lib import errors


class TimesketchExporterTest(unittest.TestCase):
  """Tests for the Threaded Timesketch exporter."""

  def testInitialization(self):
    """Tests that the processor can be initialized."""
    test_state = state.DFTimewolfState(config.Config)
    timesketch_exporter = timesketch.TimesketchExporter(test_state)
    self.assertIsNotNone(timesketch_exporter)

  # pylint: disable=invalid-name
  @mock.patch('dftimewolf.lib.timesketch_utils.GetApiClient')
  def testSetupWithSketchId(self, mock_GetApiClient):
    """Tests the SetUp function."""
    mock_sketch = mock.Mock(id=1234, my_acl=['write'])
    mock_api_client = mock.Mock()
    mock_api_client.get_sketch.return_value = mock_sketch
    mock_GetApiClient.return_value = mock_api_client
    test_state = state.DFTimewolfState(config.Config)
    timesketch_exporter = timesketch.TimesketchExporter(test_state)
    timesketch_exporter.SetUp(
        incident_id=None,
        sketch_id=1234,
        analyzers=None
    )
    self.assertEqual(timesketch_exporter.sketch_id, 1234)
    mock_api_client.get_sketch.assert_called_with(1234)

  # pylint: disable=invalid-name
  @mock.patch('dftimewolf.lib.timesketch_utils.GetApiClient')
  def testSetupWithReadonlySketchId(self, mock_GetApiClient):
    """Tests the SetUp function."""
    mock_sketch = mock.Mock(id=1234, my_acl=['read'])
    mock_api_client = mock.Mock()
    mock_api_client.get_sketch.return_value = mock_sketch
    mock_GetApiClient.return_value = mock_api_client
    test_state = state.DFTimewolfState(config.Config)
    timesketch_exporter = timesketch.TimesketchExporter(test_state)
    with self.assertRaises(errors.DFTimewolfError) as error:
      timesketch_exporter.SetUp(
          incident_id=None,
          sketch_id=1234,
          analyzers=None
      )

    self.assertEqual(
        error.exception.message, 'No write access to sketch ID 1234, aborting')

  # pylint: disable=invalid-name
  @mock.patch('timesketch_import_client.importer.ImportStreamer')
  @mock.patch('dftimewolf.lib.timesketch_utils.GetApiClient')
  def testNewSketchCreation(self, mock_GetApiClient, _):
    """Tests the SetUp function."""
    mock_sketch = mock.Mock(id=1234, my_acl=['write'])
    mock_sketch.api.api_root = 'timesketch.com/api/v1'
    mock_api_client = mock.Mock()
    mock_api_client.get_sketch.return_value = None
    mock_api_client.create_sketch.return_value = mock_sketch
    mock_GetApiClient.return_value = mock_api_client
    test_state = state.DFTimewolfState(config.Config)
    test_state.recipe = {'name': 'test_recipe'}
    timesketch_exporter = timesketch.TimesketchExporter(test_state)
    timesketch_exporter.SetUp(
        incident_id=None,
        sketch_id=None,
        analyzers=None
    )
    test_container = containers.File('file.ext', '/tmp/file.ext')
    timesketch_exporter.PreProcess()
    timesketch_exporter.Process(test_container)
    timesketch_exporter.PostProcess()
    self.assertEqual(timesketch_exporter.sketch_id, 1234)
    mock_api_client.create_sketch.assert_called_with(
      'Untitled sketch', 'Sketch generated by dfTimewolf')
    report = timesketch_exporter.state.GetContainers(containers.Report)[0]
    self.assertEqual(report.module_name, 'TimesketchExporter')
    self.assertEqual(
        report.text,
        'Your Timesketch URL is: timesketch.com/sketches/1234/')
    self.assertEqual(report.text_format, 'markdown')

  # pylint: disable=invalid-name
  @mock.patch('time.sleep')
  @mock.patch('timesketch_import_client.importer.ImportStreamer')
  @mock.patch('dftimewolf.lib.timesketch_utils.GetApiClient')
  def testWaitForTimeline(
        self, mock_GetApiClient, unused_streamer, unused_sleep):
    """Tests the SetUp function."""
    mock_sketch = mock.Mock(id=1234, my_acl=['write'])
    mock_sketch.api.api_root = 'timesketch.com/api/v1'

    mock_api_client = mock.Mock()
    mock_api_client.get_sketch.return_value = mock_sketch
    mock_api_client.create_sketch.return_value = mock_sketch
    # We also mock the attributes for the underlying .client object
    mock_api_client.client.get_sketch.return_value = mock_sketch
    mock_api_client.client.create_sketch.return_value = mock_sketch
    mock_GetApiClient.return_value = mock_api_client

    mock_timeline = mock.Mock()
    mock_timeline.status = 'ready'

    mock_sketch.list_timelines.return_value = [mock_timeline]

    test_state = state.DFTimewolfState(config.Config)
    test_state.recipe = {'name': 'test_recipe'}
    timesketch_exporter = timesketch.TimesketchExporter(test_state)
    timesketch_exporter.SetUp(
        incident_id=None,
        sketch_id=None,
        analyzers=None,
        wait_for_timelines=True
    )
    test_container = containers.File('file.ext', '/tmp/file.ext')
    timesketch_exporter.PreProcess()
    timesketch_exporter.Process(test_container)
    timesketch_exporter.PostProcess()
    mock_sketch.list_timelines.assert_called_once()


if __name__ == '__main__':
  unittest.main()
