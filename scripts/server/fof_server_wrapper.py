import os
import pty
import subprocess
import asyncio
import fcntl
import termios
import signal

class FofServerWrapper:
    def __init__(self, launch_cmd, debug=False):
        self.launch_cmd = launch_cmd
        self.debug = debug
        self.leader_fd = None
        self.fof_proc = None
        self.oldsignal = None

    def restrict_interrupt(self):
        self.oldsignal = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, signal.default_int_handler)

    def unrestrict_interrupt(self):
        if self.oldsignal is not None:
            signal.signal(signal.SIGINT, self.oldsignal)

    async def start(self):
        if os.getuid() == 0:
            print(f"Do not run as root. Exiting.")
            return
        if self.launch_cmd is None:
            print("Can't start server - no launch command!")
            return

        # Launching subprocess
        self.leader_fd, follower_fd = pty.openpty()

        def setsid_and_setctty():
            os.setsid()
            fcntl.ioctl(follower_fd, termios.TIOCSCTTY, 0)

        self.fof_proc = subprocess.Popen(
            self.launch_cmd,
            preexec_fn=setsid_and_setctty,
            stdin=follower_fd,
            stdout=follower_fd,
            stderr=follower_fd,
            env=os.environ.copy()
        )

        os.close(follower_fd)

        if self.debug:
            print("[FofServerWrapper] Server process started.")

    async def read_lines(self):
        """Yields output lines from the server as they come in."""
        loop = asyncio.get_running_loop()
        try:
            buffer = ""
            while True:
                # Reading text output
                try:
                    data = await asyncio.wait_for(loop.run_in_executor(None, os.read, self.leader_fd, 4096), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except (KeyboardInterrupt, asyncio.CancelledError) as e:
                    break
                except OSError as e:
                    if e.errno == 5: break
                    raise
                if not data:
                    break
                text = data.decode(errors='ignore')

                # Splitting on lines; only sending completed lines
                lines = (buffer + text).split("\n")
                buffer = lines[-1]
                for line in lines[:-1]: yield line

        except asyncio.CancelledError:
            raise

        except Exception as e:
            if self.debug:
                print(f"[FofServerWrapper] Error while reading output: {e}")

    def send_command(self, command):
        os.write(self.leader_fd, bytes(f"{command}\n", "utf-8"))

    async def shutdown(self):
        if self.debug:
            print(f"[FofServerWrapper] Shutting down server (PID={self.fof_proc.pid}, PGID={os.getpgid(self.fof_proc.pid)})...")

        # Attempt graceful shutdown via leader_fd
        try:
            self.send_command("quit")
        except Exception as e:
            if self.debug:
                print(f"[FofServerWrapper] Error running quit: {e}")

        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, self.fof_proc.wait),
                timeout=5
            )
            if self.debug:
                print("[FofServerWrapper] Server process exited cleanly after quit command.")
        except asyncio.TimeoutError:
            # Failed quit attempt, kill process group
            if self.debug:
                print("[FofServerWrapper] Server did not exit cleanly, force-killing process group.")
            try:
                pgid = os.getpgid(self.fof_proc.pid)
                os.killpg(pgid, signal.SIGTERM)
                if self.debug:
                    print(f"[FofServerWrapper] Sent SIGTERM to PGID {pgid}.")
            except Exception as e:
                if self.debug:
                    print(f"[FofServerWrapper] Failed to kill process group: {e}")
            try:
                await asyncio.wait_for(
                    loop.run_in_executor(None, self.fof_proc.wait),
                    timeout=2
                )
            except Exception:
                if self.fof_proc.poll() is None:
                    if self.debug:
                        print(f"[FofServerWrapper] Still alive, killing process {self.fof_proc.pid} directly.")
                    self.fof_proc.kill()
                    try:
                        await asyncio.wait_for(
                            loop.run_in_executor(None, self.fof_proc.wait),
                            timeout=2
                        )
                    except Exception:
                        if self.debug:
                            print("[FofServerWrapper] Could not kill server process.")
        os.close(self.leader_fd)

        if self.debug:
            print("[FofServerWrapper] Server process shut down.")

if __name__ == "__main__":
    async def main():
        import yaml
        from dotenv import load_dotenv

        with open("configs/server-wrapper.yml", "r") as fp:
            config = yaml.safe_load(fp)
        load_dotenv("configs/server-wrapper.env")
        load_dotenv("configs/server-wrapper-secrets.env")

        rcon_addr = config.get("fof_rcon_address", "127.0.1.1")
        rcon_port = config.get("fof_rcon_port", 27015)
        rcon_password = os.environ.get("FOF_RCON_PASSWORD", "")

        starting_map = config.get("starting_map", "fof_fistful")
        max_players = str(config.get("max_players", "20"))
        server_port = str(config.get("server_port", "27015"))

        launch_cmd = [
            './srcds_run',
            '-game', 'fof',
            '+map', starting_map,
            '+maxplayers', max_players,
            '-debug',
            '-port', server_port
        ]

        server = FofServerWrapper(
            launch_cmd=launch_cmd,
            rcon_addr=rcon_addr,
            rcon_port=rcon_port,
            rcon_password=rcon_password,
            debug=True)

        server.restrict_interrupt()

        await server.start()
        if not server.fof_proc:
            print("[Main] Server did not start, exiting.")
            return

        try:
            async for line in server.read_lines():
                print(line)
                if "SHUTDOWN" in line:
                    print("[Main] SHUTDOWN detected in log, shutting down...")
                    break
        except KeyboardInterrupt:
            print("\n[Main] Ctrl-C pressed, shutting down...")

        await server.shutdown()

    asyncio.run(main())