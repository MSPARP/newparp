self.addEventListener("activate", function(event) {
	event.waitUntil(self.clients.claim());
	console.log("Event activated!");
});

self.addEventListener("install", function(event) {
	event.waitUntil(self.skipWaiting());
});

self.addEventListener("push", function(event) {  
	console.log("Received a push message", event);

	event.waitUntil(fetch("/api/token", {
		credentials: "same-origin"
	}).then(function(data) {
		return data.json();
	}).then(function(response) {
		fetch("/api/notifications", {
			credentials: "same-origin"
		}).then(function(response) {
			if (response.status !== 200) {  
				console.log("Looks like there was a problem. Status Code: " +  
				response.status);  
				return;
			}

			return response.json();
		}).then(function(data) {
			let latest = data.latest;

			for (let notification of data.notifications) {
				// Parse the messages inside the array of JSON blobs.
				try {
					notification = JSON.parse(notification);
				} catch (e) {
					console.error("NotificationParse:", e);
					continue;
				}

				// Ignore messages that are older than the latest and are not system pushes.
				if ((latest > notification.id) && !data.id !== -1) continue;

				// Shows the notification.
				self.clients.matchAll({  
					type: "window"  
				}).then(function(clientList) {  
					for (let client of clientList) {   
						if (client.visibilityState !== "visible" && (client.url.match(new RegExp(notification.url)))) return;

						self.registration.showNotification(notification.title, {  
							body: notification.body,
							icon: "/static/img/spinner-big.png" + "?url=" + encodeURIComponent(notification.url),
							tag: notification.tag || "newparp"
						});
					}
				});

				// Tell the server what our latest value is.
				if (notification.id !== -1) {
					fetch("/api/notifications", {
						method: "POST",
						credentials: "same-origin",
						headers: {
							"Content-type": "application/x-www-form-urlencoded"
						},
						body: "token=" + response.token + "&latest=" + notification.id
					});
				}
			}
		}).catch(function(err) {
			console.log("Fetch Error ", err);
		});
	}));
});

self.addEventListener("message", function(event) {
	var data = event.data;

	if (data.action && data.action === "subscription") {
		update_endpoint(data.subscription);
	}
});

self.addEventListener("pushsubscriptionchange", function() {
	do_subscribe();
});

function update_endpoint(subscription) {
	let endpoint = subscription.endpoint;

	fetch("/api/token", {
		credentials: "same-origin"
	}).then(function(data) {
		return data.json();
	}).then(function(response) {
		fetch("/api/notifications", {
			method: "POST",
			credentials: "same-origin",
			headers: {
				"Content-type": "application/x-www-form-urlencoded"
			},
			body: "token=" + response.token + "&endpoint=" + endpoint
		});
	});
}

function do_subscribe() {
	self.registration.pushManager.getSubscription().then(function(subscription) {
		// Do nothing if we already are subscribed to pushs.
		if (subscription) {
			update_endpoint(subscription);
			return;
		}

		self.registration.pushManager.subscribe({
			userVisibleOnly: true
		}).then(function(subscription) {
			update_endpoint(subscription);
		}).catch(function(e) {
			console.error("Push Register:", e);
		});
	});
}

function parseQueryString(queryString) {
	var qd = {};
	queryString.split("&").forEach(function (item) {
		var parts = item.split("=");
		var k = parts[0];
		var v = decodeURIComponent(parts[1]);
		(k in qd) ? qd[k].push(v) : qd[k] = [v, ];
	});

	return qd;
}

self.addEventListener("notificationclick", function(event) {  
	let url = ""; 

	// Android doesn't close the notification when you click on it  
	// See: http://crbug.com/463146  
	event.notification.close();

	// I thank Roost for the URL in icon query string idea.
	// 15 minutes of pain avoided.
	if (event.notification.icon.indexOf("?") > -1) {
		var queryString = event.notification.icon.split("?")[1];
		var query = parseQueryString(queryString);
		if (query.url && query.url.length === 1) {
			url = query.url[0];
		}
	}  

	// This looks to see if the current is already open and  
	// focuses if it is  
	event.waitUntil(
		self.clients.matchAll({  
			type: "window"  
		}).then(function(clientList) {  
			for (let client of clientList) {   
				if (client.visibilityState !== "visible" && (client.url.match(new RegExp(url)))) return client.focus();  
			}

			if (url !== "") {
				return clients.openWindow(url);
			}
		})
	);
});
