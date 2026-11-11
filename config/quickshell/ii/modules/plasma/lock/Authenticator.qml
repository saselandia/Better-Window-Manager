// SPDX-License-Identifier: GPL-2.0-or-later
// BWM: KScreenLocker contract, with signals for PAM operations; no raw LockContext property.
import QtQuick
QtObject {
 id:root
 property bool busy:false
 property bool fingerprintsConfigured:false
 property bool showFailure:false
 readonly property bool graceLocked:false
 readonly property string promptForSecret:qsTr("Password")
 readonly property string infoMessage:fingerprintsConfigured?qsTr("Place your fingerprint on the reader"):""
 readonly property string errorMessage:showFailure?qsTr("Unlocking failed"):""
 readonly property int authenticatorTypes:fingerprintsConfigured?1:0
 property bool waitingForResponse:false
 signal authenticateRequested()
 signal responseSubmitted(string text)
 signal clearRequested()
 function startAuthenticating() {
  waitingForResponse=true;
  promptForSecretChanged(); // KScreenLocker v2 themes respond from this signal.
  Qt.callLater(()=>{if(waitingForResponse){waitingForResponse=false;authenticateRequested();}});
 }
 function tryUnlock(text) {responseSubmitted(text);authenticateRequested();}
 function respond(text) {responseSubmitted(text);if(waitingForResponse){waitingForResponse=false;authenticateRequested();}}
 function cancel() {clearRequested();}
 signal failed()
 signal succeeded() // Compatibility only: LockContext alone consumes PAM success.
 onShowFailureChanged:if(showFailure)failed()
}
