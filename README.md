# nmap2obsidian
A simple python script for converting gnmap files to Obsidian canvases. Simply run nmap with the -oG (or -oA) argument to get a copy of the nmap scan in the greppable format (.gnmap). Give that gnmap file as input into this script and it'll spit out beautiful json representing that scan.

# Useage
python3 nmap2canvas.py /path/to/scan.gnmap > NewObsidianFile.canvas

# Example Output
![Sample Output](example.png)
