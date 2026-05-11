# IPCross: Monitoreo de Red Multi-Protocolo para Dynatrace

**IPCross** es una extensión nativa (Extensions 2.0) diseñada para eliminar puntos ciegos en el monitoreo de red, permitiendo visibilidad de nivel 3 a nivel 7 incluso donde el tráfico ICMP está restringido.

> [!CAUTION]
> ### ⚠️ Disclaimer de Seguridad y Certificación
> El certificado incluido en este repositorio es **exclusivamente para fines de prueba (PoC) y laboratorio**. Para entornos de producción, es **obligatorio** que cada organización genere su propio par de llaves y certificado de firma conforme a sus políticas internas.

---

## 🚀 Guía de Despliegue

### 1. Vía Dynatrace Hub (Recomendado para Operadores)
Utiliza este método si ya tienes el paquete `.zip` compilado.

* **Paso 1: Configuración en Credential Vault**
    El Tenant debe conocer el certificado antes de la subida:
    1. Ve a **Settings** > **Security** > **Credential vault**.
    2. Crea una credencial de tipo **Public certificate**.
    3. Selecciona el **Credential scope**: `Extension validation`.
    4. Sube el archivo `.pem` proporcionado.

* **Paso 2: Subida al Hub**
    1. Accede a la [Interfaz de Carga de Extensiones](https://demo.apps.dynatrace.com/ui/apps/dynatrace.classic.extensions/ui/hub/ext/add-extension).
    2. Arrastra el archivo `extension.zip`.
    3. Una vez validado, búscala en el Hub y haz clic en **Add to environment**.

### 2. Vía VS Code (Recomendado para Desarrolladores)
Para modificar la lógica o firmar con certificados propios:
1. Instala [Dynatrace Extensions for VS Code](https://github.com/dynatrace-extensions/dynatrace-extensions-vscode).
2. Clona este repositorio y abre la carpeta en VS Code.
3. Usa la función **Build & Upload** para gestionar la firma y el despliegue automáticamente.

---

## 🛠️ Configuración
1. Ve a **Settings** > **Monitoring** > **Monitored technologies**.
2. Busca **IPCross** y selecciona **Add monitoring configuration**.
3. Define el **Target**, selecciona los **Protocolos** (Checkboxes) y asigna el **ActiveGate/OneAgent** de ejecución.

---
*Idioma: [English](README.md) | [Español](README.es.md)*
