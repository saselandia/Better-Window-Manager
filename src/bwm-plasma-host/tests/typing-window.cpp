// SPDX-License-Identifier: GPL-2.0-or-later
// Disposable client, launched only by the private compositor's test runner.
#include <QGuiApplication>
#include <QQuickWindow>
#include <QKeyEvent>
#include <cstdio>

class TypingWindow : public QQuickWindow {
    int count = 0;
    void keyPressEvent(QKeyEvent *event) override {
        if (event->key() == Qt::Key_A && event->text() == "a") {
            printf("TYPED %d\n", ++count);
            fflush(stdout);
            event->accept();
        } else {
            QQuickWindow::keyPressEvent(event);
        }
    }
};

int main(int argc, char **argv) {
    QGuiApplication application(argc, argv);
    if (qEnvironmentVariable("BWM_FOCUS_NESTED") != "1") return 2;
    TypingWindow window;
    QObject::connect(&window, &QWindow::activeChanged, &window, [&] {
        printf("ACTIVE %d\n", window.isActive());
        fflush(stdout);
    });
    window.setTitle("BWM typing fixture");
    window.resize(500, 300);
    window.show();
    return application.exec();
}
