
import os

def extract_logs():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, 'logs')
    input_log = os.path.join(log_dir, 'app.log')
    output_log = os.path.join(log_dir, 'trades.log')

    print(f"Reading from: {input_log}")
    print(f"Writing to: {output_log}")

    if not os.path.exists(input_log):
        print(f"Error: Input log file not found at {input_log}")
        return

    count = 0
    try:
        with open(input_log, 'r', encoding='utf-8', errors='ignore') as infile, \
             open(output_log, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                if 'app.services.trading_executor' in line or 'app.services.pending_order_worker' in line:
                    outfile.write(line)
                    count += 1
        
        print(f"Successfully extracted {count} lines to trades.log")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_logs()
