### Use one shared external network
So services can talk to each other across compose projects.

 Create once:
> ```
> docker network create homelab
> ```

Then in each compose check:
> ```
> networks:
>   homelab:
>     external: true
> ```