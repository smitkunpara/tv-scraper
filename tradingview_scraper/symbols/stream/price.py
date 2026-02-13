"""Module providing two functions which return python generator containing trades realtime data."""

import re
import json
from typing import List
import logging
import signal
from time import sleep

from websocket import WebSocketConnectionClosedException

from tradingview_scraper.symbols.stream.stream_handler import StreamHandler
from tradingview_scraper.symbols.stream.utils import validate_symbols

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class RealTimeData:
    def __init__(self):
        """
        Initializes the RealTimeData class, setting up the WebSocket connection
        and request headers for TradingView data streaming.

        Delegates WebSocket management to StreamHandler.
        """
        ws_url = "wss://data.tradingview.com/socket.io/websocket?from=screener%2F"
        self.stream_handler = StreamHandler(websocket_url=ws_url)

    def get_ohlcv(self, exchange_symbol: str):
        """
        Returns a generator that yields OHLC data for a specified symbol in real-time.

        Args:
            exchange_symbol (str): The symbol in the format 'EXCHANGE:SYMBOL'.

        Returns:
            generator: A generator yielding OHLC data as JSON objects.
        """
        quote_session = self.stream_handler.quote_session
        chart_session = self.stream_handler.chart_session
        logging.info("Using sessions - Quote: %s, Chart: %s", quote_session, chart_session)

        self._add_symbol_to_sessions(quote_session, chart_session, exchange_symbol)

        return self._get_data()

    def _add_symbol_to_sessions(self, quote_session: str, chart_session: str, exchange_symbol: str):
        """
        Adds the specified symbol to the quote and chart sessions.
        """
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        self.stream_handler.send_message("quote_add_symbols", [quote_session, f"={resolve_symbol}"])
        self.stream_handler.send_message("resolve_symbol", [chart_session, "sds_sym_1", f"={resolve_symbol}"])
        self.stream_handler.send_message("create_series", [chart_session, "sds_1", "s1", "sds_sym_1", "1", 10, ""])
        self.stream_handler.send_message("quote_fast_symbols", [quote_session, exchange_symbol])
        self.stream_handler.send_message("create_study", [chart_session, "st1", "st1", "sds_1",
                            "Volume@tv-basicstudies-246", {"length": 20, "col_prev_close": "false"}])
        self.stream_handler.send_message("quote_hibernate_all", [quote_session])


    def get_latest_trade_info(self, exchange_symbol: List[str]):
        """
        Returns summary information about multiple symbols including last changes,
        change percentage, and last trade time.

        Args:
            exchange_symbol (List[str]): A list of symbols in the format 'EXCHANGE:SYMBOL'.

        Returns:
            generator: A generator yielding summary information as JSON objects.
        """
        quote_session = self.stream_handler.quote_session
        logging.info("Using quote session: %s", quote_session)

        self._add_multiple_symbols_to_sessions(quote_session, exchange_symbol)

        return self._get_data()

    def _add_multiple_symbols_to_sessions(self, quote_session: str, exchange_symbols: List[str]):
        """
        Adds multiple symbols to the quote session.
        """
        resolve_symbol = json.dumps({"adjustment": "splits", "currency-id": "USD", "session": "regular", "symbol": exchange_symbols[0]})
        self.stream_handler.send_message("quote_add_symbols", [quote_session, f"={resolve_symbol}"])
        self.stream_handler.send_message("quote_fast_symbols", [quote_session, f"={resolve_symbol}"])

        self.stream_handler.send_message("quote_add_symbols", [quote_session] + exchange_symbols)
        self.stream_handler.send_message("quote_fast_symbols", [quote_session] + exchange_symbols)


    def _get_data(self):
        """
        Continuously receives data from the TradingView server via the WebSocket connection.

        Yields:
            dict: Parsed JSON data received from the server.
        """
        try:
            while True:
                try:
                    sleep(1)
                    result = self.stream_handler.ws.recv()
                    # Ensure result is a string (WebSocket can return bytes)
                    if isinstance(result, bytes):
                        result = result.decode('utf-8')
                    # Check if the result is a heartbeat or actual data
                    if re.match(r"~m~\d+~m~~h~\d+$", result):
                        self.stream_handler.ws.recv()  # Echo back the message
                        logging.debug("Received heartbeat: %s", result)
                        self.stream_handler.ws.send(result)
                    else:
                        split_result = [x for x in re.split(r'~m~\d+~m~', result) if x]
                        for item in split_result:
                            if item:
                                try:
                                    yield json.loads(item)  # Yield parsed JSON data
                                except Exception as e:
                                    logging.error("Failed to parse JSON data: %s - Error: %s", item, e)
                                    continue

                except WebSocketConnectionClosedException:
                    logging.error("WebSocket connection closed. Attempting to reconnect...")
                    break  # Handle reconnection logic as needed
                except Exception as e:
                    logging.error("An error occurred: %s", e)
                    break  # Handle other exceptions as needed
        finally:
            self.stream_handler.ws.close()


# Example Usage
if __name__ == "__main__":
    # Register signal handler only when running as a script
    def signal_handler(sig, frame):
        """
        Handles keyboard interrupt signals to gracefully close the WebSocket connection.
        """
        logging.info("Keyboard interrupt received. Closing WebSocket connection.")
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    real_time_data = RealTimeData()

    exchange_symbol = ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "FXOPEN:XAUUSD"]  # Example symbol

    data_generator = real_time_data.get_latest_trade_info(exchange_symbol=exchange_symbol)

    # data_generator = real_time_data.get_ohlcv(exchange_symbol="BINANCE:BTCUSDT")

    # Iterate over the generator to get real-time data
    for packet in data_generator:
        print('-'*50)
        print(packet)
