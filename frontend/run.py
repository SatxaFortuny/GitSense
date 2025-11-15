import webview

if __name__ == '__main__':

    webview.create_window(
        'GitSense', 
        'gui.html', 
        width=800, 
        height=600
    )

    webview.start()