# IPCross: Multi-Protocol Network Monitoring for Dynatrace

**IPCross** is a native Dynatrace extension (Extensions 2.0) designed to eliminate network monitoring blind spots. It provides Layer 3 to Layer 7 visibility, even in environments where ICMP (Ping) traffic is restricted by security policies.

> [!CAUTION]
> ### ⚠️ Security Disclaimer & Certification
> The certificate provided in this repository is for **Testing (PoC) and Lab purposes only**. For production environments, it is **mandatory** for each organization to generate their own key pair and signing certificate according to their internal security standards.

---

## 🚀 Deployment Guide

### 1. Via Dynatrace Hub (Recommended for Operators)
Use this method if you have the compiled `.zip` package.

* **Step 1: Credential Vault Setup**
    The tenant must recognize the signing certificate before uploading:
    1. Go to **Settings** > **Security** > **Credential vault**.
    2. Create a new **Public certificate** credential.
    3. Set **Credential scope** to `Extension validation`.
    4. Upload the provided `.pem` file.

* **Step 2: Upload to Hub**
    1. Access the [Extension Upload UI](https://demo.apps.dynatrace.com/ui/apps/dynatrace.classic.extensions/ui/hub/ext/add-extension).
    2. Drag and drop the `extension.zip` file.
    3. Once validated, find **IPCross** in the Hub and click **Add to environment**.

### 2. Via VS Code (Recommended for Developers)
To modify logic or re-sign the extension:
1. Install the [Dynatrace Extensions for VS Code](https://github.com/dynatrace-extensions/dynatrace-extensions-vscode).
2. Clone this repo and open the folder in VS Code.
3. Use the **Build & Upload** function to handle signing and deployment automatically.

---

## 🛠️ Configuration
1. Go to **Settings** > **Monitoring** > **Monitored technologies**.
2. Find **IPCross** and click **Add monitoring configuration**.
3. Select your **Target**, choose your **Connection Methods** (Checkboxes), and assign an **ActiveGate/OneAgent**.

---
*Language: [English](README.md) | [Español](README.es.md)*
