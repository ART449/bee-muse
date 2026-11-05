import SwiftUI
import WebKit

/// Mantiene un único WKWebView para que la barra pueda ordenar atrás y recarga.
/// Sin puentes JavaScript, sin archivos locales y sin excepciones TLS.
final class WebViewStore: NSObject, ObservableObject, WKNavigationDelegate, WKUIDelegate {
    @Published var status: String = "Navegador Bee-Muse · HTTPS"
    @Published var canGoBack: Bool = false

    let webView: WKWebView

    override init() {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.allowsInlineMediaPlayback = true
        webView = WKWebView(frame: .zero, configuration: configuration)
        super.init()
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true
    }

    func load(_ url: URL) {
        webView.load(URLRequest(url: url))
    }

    func goBack() {
        if webView.canGoBack { webView.goBack() }
    }

    func reload() {
        webView.reload()
    }

    // MARK: WKNavigationDelegate

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url,
              GatewayURL.validate(url.absoluteString) != nil else {
            status = "Esta dirección no se abre en Bee-Muse."
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        let title = webView.title ?? ""
        status = title.isEmpty ? (webView.url?.absoluteString ?? "") : title
        canGoBack = webView.canGoBack
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        status = "No se pudo cargar: \(error.localizedDescription)"
        canGoBack = webView.canGoBack
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        status = "No se pudo conectar: \(error.localizedDescription)"
        canGoBack = webView.canGoBack
    }

    // MARK: WKUIDelegate

    /// Las ventanas emergentes se abren en la misma vista si cumplen la regla HTTPS.
    func webView(_ webView: WKWebView,
                 createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = navigationAction.request.url, GatewayURL.validate(url.absoluteString) != nil {
            webView.load(URLRequest(url: url))
        }
        return nil
    }
}

struct WebView: UIViewRepresentable {
    @ObservedObject var store: WebViewStore

    func makeUIView(context: Context) -> WKWebView {
        store.webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}
}
