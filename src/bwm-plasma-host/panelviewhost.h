// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <PlasmaQuick/ContainmentView>
#include <Plasma/Theme>
#include <QPointer>
#include <QScreen>
#include <QPropertyAnimation>
#include <QTimer>
#include <QVariantMap>
#include <memory>
#include <atomic>
class PanelSession;
class PanelViewSettings;
class PanelConfigView;
class WidgetExplorerView;
namespace PlasmaQuick {class AppletQuickItem;}

// The original shell registers PanelView's enum metadata under this URI. Only the
// enum contract is provided here; this does not register a replacement PanelView.
class PanelViewEnums : public QObject {
    Q_OBJECT
public:
    enum VisibilityMode {NormalPanel=0,AutoHide,DodgeWindows,WindowsGoBelow};Q_ENUM(VisibilityMode)
    enum OpacityMode {Adaptive=0,Opaque,Translucent};Q_ENUM(OpacityMode)
    enum LengthMode {FillAvailable=0,FitContent,Custom};Q_ENUM(LengthMode)
};

// Adapter for the installed, unmodified plasma.desktop views/Panel.qml. Preview
// surfaces never reserve work area. The explicit native-policy test can request
// reservations; neither mode implements autohide or claims a KWin task backend.
class PanelViewHost : public PlasmaQuick::ContainmentView {
    friend class PanelRuntime; // Reports output-move errors on the view, like its own setters.
    Q_OBJECT
    Q_PROPERTY(int thickness READ thickness WRITE setThickness NOTIFY geometryPolicyChanged)
    Q_PROPERTY(int length READ length WRITE setLength NOTIFY geometryPolicyChanged)
    Q_PROPERTY(int lengthMode READ lengthMode WRITE setLengthMode NOTIFY placementChanged)
    Q_PROPERTY(int alignment READ alignment WRITE setAlignment NOTIFY placementChanged)
    Q_PROPERTY(int offset READ offset WRITE setOffset NOTIFY placementChanged)
    Q_PROPERTY(int minimumLength READ minimumLength WRITE setMinimumLength NOTIFY geometryPolicyChanged)
    Q_PROPERTY(int maximumLength READ maximumLength WRITE setMaximumLength NOTIFY geometryPolicyChanged)
    Q_PROPERTY(int minThickness READ minThickness NOTIFY geometryPolicyChanged)
    Q_PROPERTY(QScreen *screenToFollow READ screenToFollow WRITE setScreenToFollow NOTIFY screenToFollowChanged)
    Q_PROPERTY(bool adaptiveOpacityEnabled READ adaptiveOpacityEnabled NOTIFY adaptiveOpacityEnabledChanged)
    Q_PROPERTY(bool unsupportedConfiguration READ unsupportedConfiguration CONSTANT)
    Q_PROPERTY(QString unsupportedConfigurationDescription READ unsupportedConfigurationDescription CONSTANT)
    Q_PROPERTY(bool userConfiguring READ userConfiguring NOTIFY userConfiguringChanged)
    Q_PROPERTY(int opacityMode READ opacityMode WRITE setOpacityMode NOTIFY policyChanged)
    Q_PROPERTY(int visibilityMode READ visibilityMode WRITE setVisibilityMode NOTIFY policyChanged)
    Q_PROPERTY(bool floating READ floating WRITE setFloating NOTIFY policyChanged)
    Q_PROPERTY(bool floatingApplets READ floatingApplets WRITE setFloatingApplets NOTIFY policyChanged)
    Q_PROPERTY(int backgroundHints READ backgroundHints WRITE setBackgroundHints NOTIFY backgroundHintsChanged)
    Q_PROPERTY(int enabledBorders READ enabledBorders NOTIFY policyChanged)
    Q_PROPERTY(QString error READ error NOTIFY errorChanged)
    Q_PROPERTY(QVariantMap viewSettings READ viewSettings NOTIFY viewSettingsChanged)
public:
    explicit PanelViewHost(Plasma::Corona *corona, QString viewSettingsFile=QStringLiteral("plasmashellrc"));
    ~PanelViewHost()override;
    static void registerTypes();
    bool load(Plasma::Containment *containment);
    PanelSession *panelSession()const;
    QString error()const{return m_error;}
    QVariantMap capabilities()const;
    // A submitted Qt frame is not proof of presentation by the compositor.
    QVariantMap presentationState()const;
    QVariantMap viewSettings()const;
    Q_INVOKABLE bool reloadViewSettings();
    Q_INVOKABLE bool applyViewSettings(const QVariantMap &changes);
    int thickness()const{return m_thickness;}
    void setThickness(int value);
    int length()const{return m_length;}
    void setLength(int value);
    bool setLengthRange(int minimum,int maximum);
    int lengthMode()const{return m_lengthMode;}
    void setLengthMode(int value);
    int alignment()const{return m_alignment;}
    void setAlignment(int value);
    int offset()const{return m_offset;}
    void setOffset(int value);
    int minimumLength()const{return m_minimumLength;}
    void setMinimumLength(int value);
    int maximumLength()const{return m_maximumLength;}
    void setMaximumLength(int value);
    int minThickness()const;
    QScreen *screenToFollow()const{return screen();}
    void setScreenToFollow(QScreen *screen);
    // PanelView 6.7.5: whether the Plasma style offers opacity options (its
    // solid/translucent variants). Choosing Adaptive is still refused below.
    bool adaptiveOpacityEnabled()const{return m_theme.adaptiveTransparencyEnabled();}
    bool unsupportedConfiguration()const{return false;}
    QString unsupportedConfigurationDescription()const{return {};}
    Q_INVOKABLE void fixUnsupportedConfiguration(){}
    // Asks the owner (runtime) to create a copy; without one the request fails visibly.
    Q_INVOKABLE void clonePanelTo(int location,QScreen *screen);
    // While the original Panel Settings are open, QML edits persist like PanelView;
    // otherwise these setters remain preview-only (R4 contract).
    bool userConfiguring()const{return m_userConfiguring;}
    // R5: the original "Add Widgets" side bar of this panel, created on first use.
    WidgetExplorerView *widgetExplorer()const;
    bool toggleWidgetExplorer();
    void setUserConfiguring(bool value);
    int visibilityMode()const{return m_visibility;}
    void setVisibilityMode(int value);
    int opacityMode()const{return m_opacity;}
    void setOpacityMode(int value);
    bool floating()const{return m_floating;}
    void setFloating(bool value);
    bool floatingApplets()const{return m_floatingApplets;}
    void setFloatingApplets(bool value);
    int backgroundHints()const{return m_backgroundHints;}
    void setBackgroundHints(int value);
    int enabledBorders()const;
    Q_INVOKABLE QRect dogdeGeometryByDistance(int distance)const;
Q_SIGNALS:
    void geometryPolicyChanged();
    void policyChanged();
    void backgroundHintsChanged();
    void errorChanged();
    void viewSettingsChanged();
    void placementChanged();
    void screenToFollowChanged();
    void userConfiguringChanged();
    void adaptiveOpacityEnabledChanged();
    void cloneRequested(int location,QScreen *screen);
    // The runtime moves the panel to that output (bindings are by description).
    void screenToFollowRequested(QScreen *target);
protected:
    void showConfigurationInterface(Plasma::Applet *applet)override;
    bool event(QEvent *event)override;
private Q_SLOTS:
    void reflow();
    void adoptLocation(Plasma::Types::Location location);
    void animateFloating();
    void updateMask();
private:
    void setError(const QString &message);
    void invalidateFrame();
    bool vertical()const;
    void useViewSettings(const QVariantMap &values);
    bool persist(const QVariantMap &changes);
    int lengthExtent(int side)const;
    QString settingsScope()const;
    QPointer<PlasmaQuick::AppletQuickItem> m_item;
    QPointer<PanelSession> m_session;
    QPointer<PanelConfigView> m_configView;
    QPointer<WidgetExplorerView> m_widgetExplorer;
    QPropertyAnimation m_floatingAnimation;
    QTimer m_reflow;
    int m_thickness=48,m_requestedThickness=48,m_length=640;
    int m_minimumLength=640,m_maximumLength=640;
    int m_opacity=PanelViewEnums::Translucent,m_backgroundHints=0;
    int m_visibility=PanelViewEnums::WindowsGoBelow;
    // PanelView 6.7.5 defaults: AlignLeft, FillAvailable, no offset.
    int m_alignment=Qt::AlignLeft,m_lengthMode=PanelViewEnums::FillAvailable,m_offset=0;
    bool m_userConfiguring=false;
    Plasma::Theme m_theme;
    bool m_floating=false,m_floatingApplets=false,m_lastVertical=false;
    QString m_error,m_viewSettingsFile;
    struct Frames {
        std::atomic<quint64> surface{1},rendering{0},submitted{0};
    };
    std::shared_ptr<Frames> m_frames=std::make_shared<Frames>();
    QString m_renderError;
    QUrl m_nativeSource;
    std::unique_ptr<PanelViewSettings> m_settings;
    QVariantMap m_settingsDefaults;
};
