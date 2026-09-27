"""Tests for run_in_sandbox's cleanup robustness, using a fake Docker
client/container so no real daemon is needed."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import docker

from contracts import ExecutionPhase
from system.sandbox.docker_runner import run_in_sandbox


def _fake_client_and_container(*, remove_side_effect=None, wait_side_effect=None):
    container = MagicMock()
    container.id = "fake-container-id"
    container.wait.return_value = {"StatusCode": 0}
    if wait_side_effect is not None:
        container.wait.side_effect = wait_side_effect
    container.logs.return_value = b""
    container.diff.return_value = []
    if remove_side_effect is not None:
        container.remove.side_effect = remove_side_effect

    client = MagicMock()
    client.containers.create.return_value = container
    client.images.get.return_value = MagicMock()  # image already present
    return client, container


@patch("system.sandbox.docker_runner._client")
def test_remove_failure_does_not_crash_the_run(mock_client_factory):
    client, container = _fake_client_and_container(
        remove_side_effect=docker.errors.APIError("simulated daemon race")
    )
    mock_client_factory.return_value = client

    evidence = run_in_sandbox(
        candidate_code="print('hi')",
        payload="test",
        hypothesis_id="hyp-1",
        run_id="run-1",
        phase=ExecutionPhase.BEFORE,
    )

    assert evidence.exit_code == 0
    container.remove.assert_called_once_with(force=True)


@patch("system.sandbox.docker_runner._client")
def test_kill_failure_on_timeout_does_not_crash_the_run(mock_client_factory):
    client, container = _fake_client_and_container(
        wait_side_effect=Exception("simulated timeout")
    )
    container.kill.side_effect = docker.errors.APIError("already exited")
    mock_client_factory.return_value = client

    evidence = run_in_sandbox(
        candidate_code="print('hi')",
        payload="test",
        hypothesis_id="hyp-1",
        run_id="run-1",
        phase=ExecutionPhase.BEFORE,
    )

    assert evidence.exit_code == -1
    container.remove.assert_called_once_with(force=True)
