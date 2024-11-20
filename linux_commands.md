
- Directory size:
  - Total size of a directory:
    ```bash
    du -sh /path/to/directory
    ```
  - Size of each subdirectory:
    ```bash
    du -h -d 1 . | sort -h
    ```
- Github
  - Check ssh connection
    ```bash
    ssh -T git@github.com
    ```
- Poetry
  - ssh private repo with commit id
    ```bash
    poetry config experimental.system-git-client true
    ```
- EC2
  - Check disk usage:
    ```bash
    df -h
    ```
  - If /dev/root is full:
    - Check mounted volumes:
      ```bash
      lsblk
      ```
      - Example output: About 20GB is unallocated
        ``` 
        xvda     202:0    0    60G  0 disk
        ├─xvda1  202:1    0    39G  0 part /
        ├─xvda14 202:14   0     4M  0 part
        ├─xvda15 202:15   0   106M  0 part /boot/efi
        └─xvda16 259:0    0   913M  0 part /boot
        ```
    - Resizes partition:
        ```bash
        sudo growpart /dev/xvda 1
        ```
    - Resizes filesystem:
        ```bash
        sudo resize2fs /dev/xvda1
        ```
    