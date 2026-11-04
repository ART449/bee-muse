import SwiftUI

/// Barra superior con la dirección HTTPS del gateway y el navegador embebido.
/// No guarda credenciales: sólo la última dirección usada.
struct ContentView: View {
    private static let lastURLKey = "lastGatewayURL"

    @StateObject private var store = WebViewStore()
    @State private var address: String = UserDefaults.standard.string(forKey: ContentView.lastURLKey) ?? ""

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            Text(store.status)
                .font(.footnote)
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 8)
                .padding(.bottom, 4)
            Divider()
            WebView(store: store)
        }
    }

    private var toolbar: some View {
        HStack(spacing: 8) {
            TextField("Dirección HTTPS del gateway", text: $address)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .onSubmit(connect)
            Button("Conectar", action: connect)
                .buttonStyle(.borderedProminent)
            Button(action: store.goBack) { Image(systemName: "chevron.left") }
                .accessibilityLabel("Atrás")
                .disabled(!store.canGoBack)
            Button(action: store.reload) { Image(systemName: "arrow.clockwise") }
                .accessibilityLabel("Recargar")
        }
        .padding(8)
    }

    private func connect() {
        var value = address.trimmingCharacters(in: .whitespacesAndNewlines)
        if !value.contains("://") { value = "https://" + value }
        guard let url = GatewayURL.validate(value) else {
            store.status = "Usa una dirección HTTPS sin credenciales."
            return
        }
        address = url.absoluteString
        UserDefaults.standard.set(url.absoluteString, forKey: ContentView.lastURLKey)
        store.load(url)
    }
}

/// Misma regla que el cliente Android: sólo https, con host y sin usuario:contraseña.
enum GatewayURL {
    static func validate(_ value: String) -> URL? {
        guard value.count < 8192,
              let url = URL(string: value),
              url.scheme?.lowercased() == "https",
              let host = url.host, !host.isEmpty,
              url.user == nil, url.password == nil
        else { return nil }
        return url
    }
}
