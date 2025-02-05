from unittest.mock import AsyncMock, mock_open
from pytest_mock import MockerFixture

import pytest

from Client.clientGameConnection import ClientGameConnection
from Model.config import Config
from Model.multiworldDto import MultiworldDto


class TestClientGameConnection:
    _world_id: int = 1
    _config: Config = Config.get_config()

    @pytest.fixture
    def client_game_connection_fixture(self, mocker: MockerFixture):
        mocker.patch('View.guiWriter.GuiWriter.write')
        mocker.patch('Client.clientGameConnection.PlayerInventory')
        console_handler = mocker.patch('Client.clientGameConnection.DolphinGameHandler')
        mocker.patch('Client.clientGameConnection.Random')
        mocker.patch('Client.clientGameConnection.MultiworldDto')
        asyncio = mocker.patch('Client.clientGameConnection.asyncio')
        mocker.patch('builtins.open', mock_open(read_data="{}"))
        asyncio.sleep = AsyncMock()
        asyncio.create_task = AsyncMock()
        return {
            "console_handler": console_handler
        }

    @pytest.mark.asyncio
    async def test_process_items(self, client_game_connection_fixture):
        console_handler_instance = client_game_connection_fixture["console_handler"].return_value
        console_handler_instance.pass_item = AsyncMock()

        client_game_connection = ClientGameConnection(self._world_id, config=self._config)

        client_game_connection._items_to_process = [MultiworldDto(0, 0, 0)]

        assert len(client_game_connection._items_to_process) == 1
        await client_game_connection.process_items()

        assert len(client_game_connection._items_to_process) == 0

    class TestConnect:
        _world_id = 1
        _config: Config = Config.get_config()

        @pytest.mark.asyncio
        async def test_is_connected(self, client_game_connection_fixture, mocker: MockerFixture):
            console_handler_instance = client_game_connection_fixture["console_handler"].return_value
            console_handler_instance.is_connected = AsyncMock(side_effet=True)

            client_game_connection = ClientGameConnection(self._world_id, config=self._config)
            handle_mock = mocker.patch.object(client_game_connection, 'handle')

            await client_game_connection.connect()

            console_handler_instance.is_connected.assert_awaited_once()
            handle_mock.assert_called_once()

        @pytest.mark.asyncio
        async def test_is_connected_retry(self, client_game_connection_fixture, mocker: MockerFixture):
            console_handler_instance = client_game_connection_fixture["console_handler"].return_value

            console_handler_instance.is_connected = AsyncMock(side_effect=[False, False, True])

            console_handler_instance.connect = AsyncMock(side_effect=[False, True])
            client_game_connection = ClientGameConnection(self._world_id, config=self._config)
            handle_mock = mocker.patch.object(client_game_connection, 'handle')

            await client_game_connection.connect()

            assert console_handler_instance.is_connected.await_count == 3
            assert console_handler_instance.connect.await_count == 1
            handle_mock.assert_called_once()

    def test_get_item_to_send(self, client_game_connection_fixture):
        client_game_connection = ClientGameConnection(self._world_id, config=self._config)
        client_game_connection._items_to_send = [MultiworldDto(0, 0, 0)]

        result = client_game_connection.get_item_to_send()

        assert result == [MultiworldDto(0, 0, 0)]

    def test_remove_item_to_send(self, client_game_connection_fixture):
        client_game_connection = ClientGameConnection(self._world_id, config=self._config)
        client_game_connection._items_to_send = [MultiworldDto(5, 5, 5), MultiworldDto(10, 10, 10)]

        client_game_connection.remove_item_to_send(MultiworldDto(5, 5, 5))

        assert client_game_connection._items_to_send == [MultiworldDto(10, 10, 10)]

    def test_push_item_to_process(self, client_game_connection_fixture):
        client_game_connection = ClientGameConnection(self._world_id, config=self._config)
        client_game_connection._items_to_process = [MultiworldDto(0, 0, 0)]

        client_game_connection.push_item_to_process(MultiworldDto(5, 5, 5))

        assert client_game_connection._items_to_process == [MultiworldDto(0, 0, 0), MultiworldDto(5, 5, 5)]