# Direct Ethernet Connection Between PC and Raspberry Pi (Ubuntu)

## Step 1 — Direct Ethernet Connection (RJ45 Cable)

Connect the Ethernet cable directly between the **Raspberry Pi** and your **computer**.

### On your computer (Ubuntu):

1. Open **Settings** → **Network**
2. Locate the **Wired** connection
3. Open the **IPv4** tab
4. Change **Method** from **Automatic (DHCP)** to **Shared to other computers**
5. Click **Apply**
6. Disable and re-enable the wired connection to restart the interface

### What does this do?
Your computer will create a **private local network** and automatically assign an IP address to the Raspberry Pi.  
This avoids common issues with university Wi-Fi networks, such as restricted access and frequently changing IP addresses.

---

## Step 2 — Discover the Raspberry Pi and Connect via SSH

Wait approximately **30 seconds** for the network to initialize.

### Option 1 — Ping using mDNS (hostname resolution)

```bash
ping ubuntu.local
```

If the Raspberry Pi responds, connect directly:

```bash
ssh ubuntu@ubuntu.local
```

---

### Option 2 — Discover the IP address manually

List devices on the local network:

```bash
arp -a
```

Identify the IP address assigned to the Raspberry Pi (typically `10.42.0.X`) and connect:

```bash
ssh ubuntu@10.42.0.X
```

---

## Notes
- Default username: `ubuntu`
- Ensure the Raspberry Pi is powered on before connecting the Ethernet cable
- If `ubuntu.local` does not resolve, use the `arp -a` method
