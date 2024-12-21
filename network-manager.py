import curses
import time
import subprocess
import os
import re
from curses import wrapper
import threading
import netifaces
import wifi

class NetworkManagerTUI:
    def __init__(self):
        self.menu_items = ['WiFi Networks', 'Ethernet', 'Network Info', 'DNS Settings', 'Quit']
        self.current_row = 0
        self.wifi_networks = []
        self.scanning = False

    def get_wifi_networks(self):
       
        try:
            wifi_scanner = wifi.Cell.all('wlan0')
            networks = []
            for network in wifi_scanner:
                networks.append({
                    'ssid': network.ssid,
                    'signal': network.signal,
                    'encrypted': network.encrypted,
                    'encryption_type': network.encryption_type if network.encrypted else 'None'
                })
            return networks
        except Exception as e:
            return []

    def get_network_interfaces(self):
     
        return netifaces.interfaces()

    def get_ip_address(self, interface):
 
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                return addrs[netifaces.AF_INET][0]['addr']
            return "No IP"
        except:
            return "Error"

    def connect_wifi(self, ssid, password):

        try:
            subprocess.run(['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password])
            return True
        except:
            return False

    def print_center(self, stdscr, text):

        height, width = stdscr.getmaxyx()
        x = width//2 - len(text)//2
        y = height//2
        stdscr.addstr(y, x, text)

    def draw_menu(self, stdscr):
   
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
    
        title = "Network Manager TUI"
        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, start_x_title, title)
        stdscr.attroff(curses.color_pair(2))

  
        for idx, item in enumerate(self.menu_items):
            x = int(width//2 - len(item)//2)
            y = int(height//2 - len(self.menu_items)//2 + idx)
            
            if idx == self.current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, item)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, item)

        stdscr.refresh()

    def wifi_menu(self, stdscr):
        """Show WiFi networks menu"""
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

       
            if not self.wifi_networks:
                self.print_center(stdscr, "Scanning for networks...")
                stdscr.refresh()
                self.wifi_networks = self.get_wifi_networks()
                continue

       
            for idx, network in enumerate(self.wifi_networks):
                ssid = network['ssid']
                signal = network['signal']
                encrypted = "🔒" if network['encrypted'] else "🔓"
                
          
                network_info = f"{ssid} {encrypted} ({signal}dBm)"
                x = int(width//2 - len(network_info)//2)
                y = idx + 2

                if network['encrypted']:
                    stdscr.attron(curses.color_pair(4))
                else:
                    stdscr.attron(curses.color_pair(3))
                
                stdscr.addstr(y, x, network_info)
                
                stdscr.attroff(curses.color_pair(3))
                stdscr.attroff(curses.color_pair(4))

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP and self.current_row > 0:
                self.current_row -= 1
            elif key == curses.KEY_DOWN and self.current_row < len(self.wifi_networks)-1:
                self.current_row += 1
            elif key == ord('\n'):
             
                selected_network = self.wifi_networks[self.current_row]
                if selected_network['encrypted']:
         
                    curses.echo()
                    stdscr.addstr(height-2, 0, "Enter password: ")
                    password = stdscr.getstr().decode('utf-8')
                    curses.noecho()
                    
              
                    if self.connect_wifi(selected_network['ssid'], password):
                        self.print_center(stdscr, "Connected!")
                    else:
                        self.print_center(stdscr, "Connection failed!")
                    stdscr.refresh()
                    time.sleep(2)
                else:
              
                    if self.connect_wifi(selected_network['ssid'], ''):
                        self.print_center(stdscr, "Connected!")
                    else:
                        self.print_center(stdscr, "Connection failed!")
                    stdscr.refresh()
                    time.sleep(2)
            elif key == ord('q'):
                break

        
            if not self.scanning:
                self.scanning = True
                threading.Thread(target=self.refresh_networks).start()

    def refresh_networks(self):
     
        time.sleep(10)  
        self.wifi_networks = self.get_wifi_networks()
        self.scanning = False

    def ethernet_menu(self, stdscr):

        while True:
            stdscr.clear()
            interfaces = [iface for iface in self.get_network_interfaces() if iface.startswith('eth')]
            
            for idx, iface in enumerate(interfaces):
                ip = self.get_ip_address(iface)
                info = f"{iface}: {ip}"
                stdscr.addstr(idx + 2, 2, info)

            stdscr.refresh()
            if stdscr.getch() == ord('q'):
                break

    def network_info(self, stdscr):

        while True:
            stdscr.clear()
            y = 2

  
            stdscr.addstr(y, 2, "Network Interfaces:", curses.A_BOLD)
            y += 2
            
            for iface in self.get_network_interfaces():
                ip = self.get_ip_address(iface)
                info = f"{iface}: {ip}"
                stdscr.addstr(y, 4, info)
                y += 1

    
            y += 1
            stdscr.addstr(y, 2, "DNS Servers:", curses.A_BOLD)
            y += 2
            
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if 'nameserver' in line:
                            stdscr.addstr(y, 4, line.strip())
                            y += 1
            except:
                stdscr.addstr(y, 4, "Could not read DNS information")

            stdscr.refresh()
            if stdscr.getch() == ord('q'):
                break

    def dns_settings(self, stdscr):
     
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            options = ['Add DNS Server', 'Remove DNS Server', 'View Current DNS', 'Back']
            for idx, option in enumerate(options):
                x = int(width//2 - len(option)//2)
                y = int(height//2 - len(options)//2 + idx)
                
                if idx == self.current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, option)
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, x, option)

            stdscr.refresh()
            key = stdscr.getch()

            if key == ord('q'):
                break
            elif key == curses.KEY_UP and self.current_row > 0:
                self.current_row -= 1
            elif key == curses.KEY_DOWN and self.current_row < len(options)-1:
                self.current_row += 1
            elif key == ord('\n'):
                if options[self.current_row] == 'Back':
                    break


    def main(self, stdscr):

        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        
        curses.curs_set(0)

        while True:
            self.draw_menu(stdscr)
            key = stdscr.getch()

            if key == curses.KEY_UP and self.current_row > 0:
                self.current_row -= 1
            elif key == curses.KEY_DOWN and self.current_row < len(self.menu_items)-1:
                self.current_row += 1
            elif key == ord('\n'):
                if self.menu_items[self.current_row] == 'Quit':
                    break
                elif self.menu_items[self.current_row] == 'WiFi Networks':
                    self.wifi_menu(stdscr)
                elif self.menu_items[self.current_row] == 'Ethernet':
                    self.ethernet_menu(stdscr)
                elif self.menu_items[self.current_row] == 'Network Info':
                    self.network_info(stdscr)
                elif self.menu_items[self.current_row] == 'DNS Settings':
                    self.dns_settings(stdscr)

def main():
  
    if os.geteuid() != 0:
        print("This program needs to be run as root!")
        return
    
    nm = NetworkManagerTUI()
    curses.wrapper(nm.main)

if __name__ == "__main__":
    main()