import signal
import sys

class SignalHandler:
    def __init__(self):
        self.stopped = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        """Handler to set the stop flag."""
        sig_name = signal.Signals(signum).name
        print(f"\nProgram received the signal: {sig_name}. Setting stop flag.")
        self.stopped = True
    
    def cleanup(self):
        """Cleanup resources before exiting."""
        print("Saving state and closing resources... Done.")
        sys.exit(0)