# Rebrand-Blizzard-App

Changes the Blizzard App icons back to Battle.net icons.



Usage
=====

There's three ways you can rebrand the Blizzard App:

- The Easy Way (my compiled executable)
- The Paranoid/Safer Way (run my python code manually)
- The Hard Way (use MPQEditor yourself)

The Easy Way
============

1. Download latest release from https://github.com/Darkman/Rebrand-Blizzard-App/releases
2. Close Blizzard/Battle.net Completely (from tray).
3. Extract and run
4. Couple Boxes to click
5. Start Battle.net


The Paranoid/Safer Way
======================
The executable I made is from the Python code in this repository, but if you don't trust the exe, then you can run the Python code manually after examining it.

1. Download latest release from https://github.com/Darkman/Rebrand-Blizzard-App/releases
2. Install Python (Python 3 only)
3. Extract, examine, and run my python code.


The Hard Way
============

1. Download latest release from https://github.com/Darkman/Rebrand-Blizzard-App/releases (to use the icon resources folder I put together)
2. Download MPQEditor from http://www.zezula.net/en/mpq/download.html
3. Create a 'RUN_ME.cmd' file with the following code:
```
copy /v /-y Battle.net.mpq Battle.net.mpq.backup

MPQEditor.exe add Battle.net.mpq resources/* resources /r
```
4. Blizzard keeps multiple installs of Battle.net in the form of "Battle.net.8554", with the number being the version (highest number = current Battle.net version).
    Put the MPQEditor.exe, my 'resources' directory, and the .cmd file next to the latest Battle.net.mpq file. 
    For example, my latest one is located at ```C:\Program Files (x86)\Battle.net\Battle.net.8554\Battle.net.mpq```
    
    So the files should look like:
    ```
    (...Other Junk...)
    Battle.net.exe
    Battle.net.mpq
    MPQEditor.exe
    RUN_ME.cmd
    resources
    (...Other Junk...)
    ```
5. Close Battle.net completely (from tray).
6. Double click the RUN_ME.cmd file to run it.
7. Restart Battle.net
