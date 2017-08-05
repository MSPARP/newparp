var msparp = (function() {

	var body = $(document.body);
	var ws_protocol = (location.protocol=="https:") ? "wss://" : "ws://";

	// Prevent breaking browsers and settings that don't like localStorage
	try {
		localStorage.setItem("supported", "yes");
		// Remember toggle box state
		$(".toggle_box > input:first-child, .group_toggle, .device_settings").change(function() {
			if (this.id) { localStorage.setItem(this.id, this.checked); }
		}).each(function() {
			if (this.id && !this.checked) { this.checked = localStorage.getItem(this.id) == "true"; }
		});
		
		if ($("#toggle_with_settings").is(':checked')) {
			$("#player_select").addClass('tabbed_select');
		}
		
		$(".character_list ul input").each(function() {
				var group = $(this).parentsUntil("#filter_settings").last();
				var group_input = group.find("legend input");
				var counter = group.find(".groupcount");
				var characters = group.find("li input");
				var checked_characters = group.find("li input:checked");
				if (checked_characters.length == 0) {
					group_input.prop("checked", false).prop("indeterminate", false);
					group_input.attr("class", "");
					counter.html("");
				} else if (checked_characters.length == characters.length) {
					group_input.prop("checked", true).prop("indeterminate", false);
					group_input.attr("class", "");
					counter.html(checked_characters.length + "/" + characters.length + "&nbsp;");
				} else {
					group_input.prop("checked", false).prop("indeterminate", true);
					group_input.attr("class","indeterminate");
					counter.html(checked_characters.length + "/" + characters.length + "&nbsp;");
				}
			});
			var localstorage = "yes";
	
	} catch (e) {var localstorage = false;}
	
	// Prevent console is undefined errors for IE9 Mobile and other horrors
	window.console = window.console || (function(){
		var c = {}; c.log = c.warn = c.debug = c.info = c.error = c.time = c.dir = c.profile = c.clear = c.exception = c.trace = c.assert = function(){};
		return c;
	})();
	
	// Detect touch devices because apple/some browsers cannot handle focus highlighting
	var touch_enabled = false;
	if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
		$("body").addClass("touch");
		touch_enabled = true;
	}
	
	// Handle expanding/collapsing descriptions on touch devices here because iOS
	$(".touch").on("click",  "#group_chats .subtitle + p, #my_chats_list .chatlist_topic, .spam_table .abridged_message", function() {
		$(this).toggleClass("expanded");
	});
	
	// Force spectrum colour picker for consistency (sigh)
	$("#color_input, #color_header_set").spectrum();
	
	// Auto focus log pages to make them scrollable on desktop
	if (!touch_enabled) {
		$("#archive_conversation #conversation_wrap").ready(function() {
			$("#archive_conversation #conversation_wrap").focus();
		});
	}
	
	// Apply toggle box state to filter & stem column, hide small toggle if open, wait for IE
	$("#toggle_search_for_characters").ready(function() {
		if ($("#toggle_search_for_characters").is(':checked')) {
			$("#filter_column").addClass("open");
			$("#stem_column").addClass("open");
			$("#toggle_filter").prop("checked", true);
			$("#small_search_toggle").hide();
		}
	});
	
	// Allow users to collapse read announcements while showing new ones
	if (localstorage && $("#announcement_text").length) {
		var current_announcement = $("#announcement_text").html();
		var read_announcement = localStorage.getItem("read_announcement"); 
		var hide_announcement = localStorage.getItem("hide_announcement");
		// only allow announcement to start out hidden if it matches
		if (read_announcement == current_announcement && hide_announcement == "yes") {
			$("#toggle_announcement").text("(reread)");
			$("#announcement_text").hide();
			$("#announcements").addClass("hide_announcement");
		}
		// if it doesn't match, reset hidden status and mark as new
		if (read_announcement !== current_announcement) {
			hide_announcement = "no";
			$(".announce_label").text("Announcements (new)");
			localStorage.setItem("hide_announcement", hide_announcement);
		}
		// initialise fadein/out
		setTimeout(function () {
			$("#announcements").addClass("init");
		}, 500);
		// update read status
		localStorage.setItem("read_announcement", current_announcement);
		
		// toggle announcement display
		$(".announcements_link").click(function() {
			if (hide_announcement == "yes") {
				$("#toggle_announcement").text("(hide)");
				$("#announcement_text").show();
				$("#announcements").removeClass("hide_announcement");
				hide_announcement = "no";
				localStorage.setItem("hide_announcement", hide_announcement);
			} else {
				$("#toggle_announcement").text("(reread)");
				$("#announcement_text").hide();
				$("#announcements").addClass("hide_announcement");
				hide_announcement = "yes";
				localStorage.setItem("hide_announcement", hide_announcement);
			}
		});
	} else {
		// if there is no localstorage, don't leave this looking clickable
		$("#announcements .announcements_link").css("cursor", "default");
		$("#announcements .announcements_link span").css("text-decoration", "none");
		$("#toggle_announcement").css("display", "none");
	}
	
	// Enable animation on these elements only when interacted with
	$(".enable_anim").click(function() {
		$(this).addClass("init_anim");
		$(this).removeClass("enable_anim");
	});

	// Enable per-device settings that don't require pre-render hooks
	var dev_user_disable_hotkeys = "false";
	var dev_user_safe_bbcode = "false";
	var dev_user_smart_quirk = "false";
	var dev_user_wrap_smart_quirks = "false";
	var dev_user_smart_action_delimiter = "*";
	var dev_user_smart_dialogue_delimiter = '"';
	
	if (localstorage) {
		$( document ).ready(function() {
			material_feedback=localStorage.getItem("material_feedback");
			if (material_feedback == "true") {
				$("body").addClass("material");
			}
			disable_animations=localStorage.getItem("disable_animations");
			if (disable_animations == "true") {
				$("body").addClass("no_moving");
			}
			disable_left_bar=localStorage.getItem("disable_left_bar");
			if (disable_left_bar == "true") {
				$("body").addClass("disable_left_bar");
			}
			collapse_padding=localStorage.getItem("collapse_padding");
			if (collapse_padding == "true") {
				$("body").addClass("collapse_padding");
			}
		});
		// Set default to safe bbcode, load delimiters if set
		if (localStorage.getItem("safe_bbcode") === null) { localStorage.setItem("safe_bbcode", "true"); }
		if (localStorage.getItem("safe_bbcode") == "true") {
			dev_user_safe_bbcode = "true";
		}
		if (localStorage.getItem("disable_hotkeys") == "true") {
			dev_user_disable_hotkeys = "true";
		}
		if (localStorage.getItem("smart_quirk") == "true") {
			dev_user_smart_quirk = "true";
		}
		if (localStorage.getItem("wrap_smart_quirks") == "true") {
			dev_user_wrap_smart_quirks = "true";
		}
		if (localStorage.getItem("smart_action_delimiter") !== null && localStorage.getItem("smart_action_delimiter") !== "") { 
			dev_user_smart_action_delimiter = localStorage.getItem("smart_action_delimiter"); 
		}
		 if (localStorage.getItem("smart_dialogue_delimiter") !== null && localStorage.getItem("smart_dialogue_delimiter") !== "") { 
			dev_user_smart_dialogue_delimiter = localStorage.getItem("smart_dialogue_delimiter"); 
		}
		
		// Update smart quirk delimiters
		$("#smart_action_delimiter").change(function() {
			localStorage.setItem("smart_action_delimiter", $("#smart_action_delimiter").val());
		});
		$("#smart_dialogue_delimiter").change(function() {
			localStorage.setItem("smart_dialogue_delimiter", $("#smart_dialogue_delimiter").val());
		});
	} 
	
	// Populate smart quirk delimiters
	$("#smart_action_delimiter").ready(function() {
		$("#smart_action_delimiter").val(dev_user_smart_action_delimiter).attr("value", dev_user_smart_action_delimiter); 
	});
	$("#smart_dialogue_delimiter").ready(function() {
		$("#smart_dialogue_delimiter").val(dev_user_smart_dialogue_delimiter).attr("value", dev_user_smart_dialogue_delimiter); 
	});
	
	// Live update when switching in settings
	$("#basic_forms").click(function() {
		$("body").toggleClass("no_forms");
	});
	$("#material_feedback").click(function() {
		$("body").toggleClass("material");
	});
	$("#disable_animations").click(function() {
		$("body").toggleClass("no_moving");
	});
	
	// Auto refresh unread counter in nav bar; use json
	//setInterval(function(){ 
	//	$.get("/unread.json", {}, function(data) {
	//		if (data.unread) {
	//			$("#unread_update").html("<a id='unread_counter' href='" + data.url + "'>" + data.unread + "</a>");
	//		} else {
	//			$("#unread_update").html("");
	//		}
	//	});
	//}, 14130);
	
	// Character info
	function update_character(data) {
		if (typeof data["search_character"]!= "undefined") {
			$("[name=search_character_id]").val(data["search_character"]["id"]);
		} else {
			$("[name=search_character_id]").val(data["id"]);
		}
		$("#toggle_with_settings").prop("checked", true).change();
		$("input[name=name]").val(data["name"]).attr("value", data["name"]); /* update attr as well for css targetting */
		$("input[name=acronym]").val(data["acronym"]).attr("value", data["acronym"]).keyup();
		$("input[name=color]").val("#"+data["color"]).change();
		$("#color_input").spectrum("set", "#" + data["color"]);
		if (!body.hasClass("chat")) {
			if (typeof data["text_preview"]!= "undefined") {
				$("#text_preview").text(data["text_preview"]);
			} else if (typeof data["search_character"]!= "undefined") {
				$("#text_preview").text(data["search_character"]["text_preview"]);
			}
		}
		if (data["quirk_prefix"] != "" || data["quirk_suffix"] != "" || data["case"] != "normal" || data["replacements"].length != 0 || data["regexes"].length != 0) {
			$("#toggle_typing_quirks").prop("checked", true).change();
		}
		$("input[name=quirk_prefix]").val(data["quirk_prefix"]);
		data["quirk_prefix"] ? $("input[name=quirk_prefix]").attr("value", data["quirk_prefix"]) : $("input[name=quirk_prefix]").removeAttr('value');
		$("input[name=quirk_suffix]").val(data["quirk_suffix"]);
		data["quirk_suffix"] ? $("input[name=quirk_suffix]").attr("value", data["quirk_suffix"]) : $("input[name=quirk_suffix]").removeAttr('value');
		$("select[name=case]").val(data["case"]);
		clear_replacements();
		if (data["replacements"].length == 0) {
			add_replacement();
		} else {
			data["replacements"].forEach(function(replacement) { add_replacement(null, replacement[0], replacement[1]); });
		}
		clear_regexes();
		if (data["regexes"].length == 0) {
			add_regex();
		} else {
			data["regexes"].forEach(function(regex) { add_regex(null, regex[0], regex[1]); });
		}
	}

	// Replacement list
	function delete_replacement(e) {
		if (this.parentNode.parentNode.childElementCount == 1) {
			add_replacement();
		}
		$(this.parentNode).remove();
		return false;
	}
	function add_replacement(e, from, to) {
		var size = body.hasClass("chat") ? 7 : 10;
		new_item = $("<li><div class=\"input fromto\"><input type=\"text\" name=\"quirk_from\" size=\"" + size + "\"></div> to <div class=\"input fromto\"><input type=\"text\" name=\"quirk_to\" size=\"" + size + "\"></div> <button type=\"button\" class=\"delete_replacement\">x</button></li>");
		if (from || to) {
			var inputs = $(new_item).find('input');
			inputs[0].value = from;
			inputs[1].value = to;
		}
		$(new_item).find('.delete_replacement').click(delete_replacement);
		$(new_item).appendTo('#replacement_list');
		return false;
	}
	function clear_replacements(e) {
		$('#replacement_list').empty();
		return false;
	}
	function clear_replacements_and_add(e) {
		$('#replacement_list').empty();
		add_replacement();
		return false;
	}

	// Regex list
	function delete_regex(e) {
		if (this.parentNode.parentNode.childElementCount == 1) {
			add_regex();
		}
		$(this.parentNode).remove();
		return false;
	}
	function add_regex(e, from, to) {
		var size = body.hasClass("chat") ? 7 : 10;
		new_item = $("<li><div class=\"input fromto\"><input type=\"text\" name=\"regex_from\" size=\"" + size + "\"></div> to <div class=\"input fromto\"><input type=\"text\" name=\"regex_to\" size=\"" + size + "\"></div> <button type=\"button\" class=\"delete_regex\">x</button></li>");
		if (from && to) {
			var inputs = $(new_item).find('input');
			inputs[0].value = from;
			inputs[1].value = to;
		}
		$(new_item).find('.delete_regex').click(delete_regex);
		$(new_item).appendTo('#regex_list');
		return false;
	}
	function clear_regexes(e) {
		$('#regex_list').empty();
		return false;
	}
	function clear_regexes_and_add(e) {
		$('#regex_list').empty();
		add_regex();
		return false;
	}

	// Event handlers for character form
	function initialize_character_form() {
		// Search character dropdown
		$("select[name=search_character_id]").change(function() {
			$.get("/search_characters/"+this.value+".json", {}, update_character);
		});
		$("select[name=id]").change(function() {
			var url = this.value[0] == "s" ? "search_characters" : "characters";
			$.get("/" + url + "/" + this.value.substr(2) + ".json", {}, update_character);
		});
		// Text preview
		var text_preview_container = $("#text_preview_container");
		var text_preview_acronym = $("#text_preview_acronym");
		$("input[name=acronym]").keyup(function() {
			if (this.value == "") {
				text_preview_acronym.text("");
			} else {
				text_preview_acronym.text(this.value + ": ");
			}
		});
		// Color and color_hex
		var color_input = $("input[name=color]").change(function() {
			color_hex_input.val(this.value.substr(1));
			text_preview_container.css("color", this.value);
		});
		var color_hex_input = $("#color_hex_input").keyup(function() {
			if (this.value.length == 6) {
				color_input.val("#" + this.value);
				color_input.spectrum("set", "#" + this.value);
				text_preview_container.css("color", "#" + this.value);
			}
		});
		// Toggle filter box
		$("#toggle_search_for_characters").change(function() {
			if ($("#toggle_search_for_characters").is(':checked')) {
				$("#filter_column").addClass("open");
				$("#stem_column").addClass("open");
				$("#toggle_filter").prop("checked", true);
				$("#small_search_toggle").hide();
			} else {
				$("#filter_column").removeClass("open");
				$("#stem_column").removeClass("open");
				$("#toggle_filter").prop("checked", false);
				$("#small_search_toggle").show();
			}
		});
		// Replacement list
		$('.delete_replacement').click(delete_replacement);
		$('#add_replacement').click(add_replacement);
		$('#clear_replacements').click(clear_replacements_and_add);
		// Regex list
		$('.delete_regex').click(delete_regex);
		$('#add_regex').click(add_regex);
		$('#clear_regexes').click(clear_regexes_and_add);
	}

	// BBCode
	var tag_properties = {bgcolor: "background-color", color: "color", font: "font-family", bshadow: "box-shadow", tshadow: "text-shadow"}
	function bbencode(text, admin) { return raw_bbencode(Handlebars.escapeExpression(text), admin); }
	function raw_bbencode(text, admin) {
		// convert BBCode inside [raw] to html escapes to prevent stacking problems and make it show with BBcode disabled
		var re = /\[raw\]([\s\S]*?)\[([\s\S]*?)\]([\s\S]*?)\[\/raw\]/ig;
		while (re.exec(text)) {
			text = text.replace(re, "[raw]$1&#91;$2&#93;$3[/raw]");
		}
		text = text.replace(/(\[[bB][rR]\])+/g, "<br>");
		// Just outright make this match case insensitive so we don't have to worry about tags matching in casing on the \2 callback
		return text.replace(/(https?:\/\/\S+)|\[([A-Za-z]+)(?:=([^\]]+))?\]([\s\S]*?)\[\/\2\]/gi, function(str, url, tag, attribute, content) {
			if (url) {
				var suffix = "";
				// Exclude a trailing closing bracket if there isn't an opening bracket.
				if (url[url.length - 1] == ")" && url.indexOf("(") == -1) {
					url = url.substr(0, url.length-1);
					suffix = ")";
				}
				url = url.replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#x27;/g, "'"); // re-escape to work with links
				return $("<a>").attr({href: ("/redirect?url=" + encodeURIComponent(url)), target: "_blank"}).text(url)[0].outerHTML + suffix;
			}
			tag = tag.toLowerCase();
			if (attribute) {
				switch (tag) {
					case "bgcolor":
					case "color":
					case "font":
						return $("<span>").css(tag_properties[tag], attribute).html(raw_bbencode(content, admin))[0].outerHTML;
					case "bshadow":
					case "tshadow":
						return admin ? $("<span>").css(tag_properties[tag], attribute).html(raw_bbencode(content, admin))[0].outerHTML : raw_bbencode(content, admin);
					case "url":
						if (attribute.substr(0, 7) == "http://" || attribute.substr(0, 8) == "https://") {
							attribute = attribute.replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#x27;/g, "'"); // re-escape to work with links
							return $("<a>").attr({href: ("/redirect?url=" + encodeURIComponent(attribute)), target: "_blank"}).html(raw_bbencode(content, admin))[0].outerHTML;
						}
						break;
				}
			} else {
				switch (tag) {
					case "b":
					case "del":
					case "i":
					case "sub":
					case "sup":
					case "u":
					case "s":
						return "<" + tag + ">" + raw_bbencode(content, admin) + "</" + tag + ">";
					case "c":
						return "<span style=\"text-transform: uppercase\">" + raw_bbencode(content, admin) + "</span>";
					case "w":
						return "<span style=\"text-transform: lowercase\">" + raw_bbencode(content, admin) + "</span>";
					case "alternian":
						return "<span class=\"alternian\">" + raw_bbencode(content, admin) + "</span>";
					case "spoiler":
						return "<label class=\"spoiler\"><input type=\"checkbox\"><span>SPOILER</span><span>" + raw_bbencode(content, admin) + "</span></label>";
					case "raw":
						return content;
				}
			}
			return "[" + tag + (attribute ? "=" + attribute : "") + "]" + raw_bbencode(content, admin) + "[/" + tag + "]";
		});
	}
	function bbremove(text) {
		text = text.replace(/(\[[bB][rR]\])+/g, "");
		return text.replace(/\[([A-Za-z]+)(?:=[^\]]+)?\]([\s\S]*?)\[\/\1\]/gi, function(str, tag, content) { return bbremove(content); });
	}

	return {
		// Registration
		"register": function() {
			$("#register_show_password_input").change(function(e) {
				$("#register_password_input, #register_password_again_input").attr("type", this.checked ? "text" : "password");
			});
		},
		// Logging in
		"log_in": function() {
			$("#log_in_show_password_input").change(function(e) {
				$("#log_in_password_input").attr("type", this.checked ? "text" : "password");
			});
			// Parse BBCode in chat info (if present)
			$(".chat_info").each(function(line) { this.innerHTML = raw_bbencode(this.innerHTML, false); });
		},
		// Homepage
		"home": function() {

			// Saved character dropdown
			$("select[name=character_id]").change(function() {
				if (this.value != "") {
					$.get("/characters/"+this.value+".json", {}, update_character);
				}
			});

			initialize_character_form();

			// Keep "be" tab appearance updated
			$(".toggle_box > #toggle_with_settings").change(function() {
				if ($("#toggle_with_settings").is(':checked')) {
					$("#player_select").addClass('tabbed_select');
				} else {
					$("#player_select").removeClass('tabbed_select');
				}
			});

			// Filter list
			function delete_filter(e) {
				if (this.parentNode.parentNode.childElementCount == 1) {
					add_filter();
				}
				$(this.parentNode).remove();
				return false;
			}
			function add_filter() {
				new_item = $("<li><div class=\"input\"><input type=\"text\" name=\"search_filter\" size=\"25\" maxlength=\"50\"></div> <button type=\"button\" class=\"delete_filter\">x</button></li>");
				$(new_item).find('.delete_filter').click(delete_filter);
				$(new_item).appendTo('#filter_list');
				return false;
			}
			function clear_filters(e) {
				$('#filter_list').empty();
				return false;
			}
			function clear_filters_and_add(e) {
				$('#filter_list').empty();
				add_filter();
				return false;
			}
			$('.delete_filter').click(delete_filter);
			$('#add_filter').click(add_filter);
			$('#clear_filters').click(clear_filters_and_add);

			// Picky checkboxes
			$(".character_list legend .input input").change(function() {
				var group = $(this).parentsUntil("#filter_settings").last();
				group.find("li input").prop("checked", this.checked);
				var characters = group.find("li input");
				var counter = group.find(".groupcount");
				var checked_characters = group.find("li input:checked");
				if (checked_characters.length > 0) {
					counter.html(checked_characters.length + "/" + characters.length + "&nbsp;");
				} else {
					counter.html("");
				}
				$(this).attr("class", "");
			});
			$(".character_list ul input").change(function() {
				var group = $(this).parentsUntil("#filter_settings").last();
				var group_input = group.find("legend input");
				var counter = group.find(".groupcount");
				var characters = group.find("li input");
				var checked_characters = group.find("li input:checked");
				if (checked_characters.length == 0) {
					group_input.prop("checked", false).prop("indeterminate", false);
					group_input.attr("class", "");
					counter.html("");
				} else if (checked_characters.length == characters.length) {
					group_input.prop("checked", true).prop("indeterminate", false);
					group_input.attr("class", "");
					counter.html(checked_characters.length + "/" + characters.length + "&nbsp;");
				} else {
					group_input.prop("checked", false).prop("indeterminate", true);
					group_input.attr("class","indeterminate");
					counter.html(checked_characters.length + "/" + characters.length + "&nbsp;");
				}
			});

		},
		// Character search
		"search": function(token) {
			var ws, ws_interval;
			$.ajaxSetup({data: {"token": token}});
			$.post("/search", {}, function(data) {
				matched = false;
				body.addClass("searching");
				searcher_id = data.id;
				ws = new WebSocket(ws_protocol + "live." + location.host + "/search/" + searcher_id);
				ws.onopen = function() {
					console.log("ready");
					ws_interval = window.setInterval(function() { console.log("ping"); ws.send("ping"); }, 10000)
				}
				ws.onmessage = function(e) {
					var data = JSON.parse(e.data);
					console.log(data);
					if (data.status == "matched") {
						matched = true;
						window.location.href = "/" + data.url;
					} else if (data.status == "quit") {
						ws.close();
					}
				}
				ws.onclose = function() {
					if (matched) { return; }
					body.removeClass("searching").addClass("search_error");
					window.clearInterval(ws_interval);
				}
			}).error(function() {
				searching = false;
				body.removeClass("searching").addClass("search_error");
			});
		},
		// Character pages
		"character": function() {
			initialize_character_form();
			var shortcut_preview = $("#shortcut_preview");
			$("#shortcut_input").keyup(function() {
				var new_shortcut = this.value.trim();
				shortcut_preview.text(new_shortcut ? "\"/" + this.value + "\"" : "the shortcut");
			});
		},
		// Search character pages
		"search_character": function() {
			initialize_character_form();
			$("#text_preview_input").keyup(function() { $("#text_preview").text(this.value); });
		},
		// Settings: log in details
		"settings_log_in_details": function() {
			$("#change_password_show_password").change(function(e) {
				$("#change_password_old_password, #change_password_new_password, #change_password_new_password_again").attr("type", this.checked ? "text" : "password");
			});
		},
		// Chat window
		"chat": function(chat, user, character_shortcuts, latest_message_id, latest_time, token) {

			$.ajaxSetup({data: {"token": token}});

			var conversation = $("#conversation");
			var chat_line_input = $("#chat_line_input input");
			var status;
			var next_chat_url;
			var user_data = {};
			if (typeof latest_time == "number") { latest_time = latest_time * 1000 }
			var latest_date = user.meta.show_timestamps ? new Date(latest_time) : null;
			var new_messages = [];

			// Connecting and disconnecting

			var ws;
			var ws_works = false;
			var ws_connected_time = 0;

			function connect() {
				if (typeof(WebSocket) == "undefined") {
					status_bar.css("color", "#f00").html("Sorry, your browser doesn't appear to support websockets. Please use the latest version of <a href=\"https://www.firefox.com/\">Firefox</a> or <a href=\"https://www.google.com/chrome\">Chrome</a> to participate in this chat.");
					return;
				}

				// Don't create a new websocket unless the previous one is closed.
				// This prevents problems with eg. double clicking the join button.
				if (ws && ws.readyState != 3) { return; }
				status = "connecting";

				ws = new WebSocket(ws_protocol + "live." + location.host + "/" + chat.id + "?after=" + latest_message_id);
				ws.onopen = function(e) { ws_works = true; ws_connected_time = Date.now(); enter(); }
				ws.onmessage = function(e) { receive_messages(JSON.parse(e.data)); }
				ws.onclose = function(e) {
					if (status == "connecting" || status == "chatting") {
						// Fall back to long polling if we've never managed to connect.
						if (!ws_works || (Date.now() - ws_connected_time) < 5000) {
							status_bar.css("color", "#f00").html("Sorry, the connection to the server has been lost.");
							return;
						}
						// Otherwise try to reconnect.
						exit();
						status_bar.css("color", "#f00").text("Sorry, the connection to the server has been lost. Attempting to reconnect...");
						window.setTimeout(connect, Math.random() * 10000);
					}
				}
			}

			function enter() {
				status = "chatting";
				window.setTimeout(ping, 10000);
				$("#disconnect_links").appendTo(document.body);
				body.addClass("chatting");
				reset_sidebar();
				if (chat.type == "pm") { refresh_pm_chat_list(); }
				refresh_my_chats_list();
				$("#send_form input, #send_form button, #sidebar_tabs button, #sidebar_left_tabs button").prop("disabled", false);
				// Auto focus chat line on non-touch devices
				if (!touch_enabled) {
					// multiply by two because Opera is weird about counting length
					var input_length = chat_line_input.val().length * 2;
					chat_line_input.focus();
					chat_line_input[0].setSelectionRange(input_length, input_length);
				}
				set_temporary_character(null);
				parse_variables();
				if (!user.meta.typing_notifications && chat.type !== "pm" && chat.type !== "roulette") {
					status_bar.css("display", "none");
				}
				status_bar.css("color", "").text((
					// Show status bar if typing notifications are available and switched on.
					user.meta.typing_notifications
					// Also always show it in PM and roulette chats for online status.
					|| chat.type == "pm" || chat.type == "roulette"
				) ? " " : "");
				text_input.keyup();
				scroll_to_bottom();
				abscond_button.text("Abscond");
			}
			function exit() {
				status = "disconnected";
				body.removeClass("chatting");
				$("#send_form input, #send_form button:not(#abscond_button), #sidebar_tabs button").prop("disabled", true);
				if (chat.type == "group") {
					info_panel.hide();
					edit_info_panel.hide();
				}
				reset_sidebar();
				status_bar.text("");
				abscond_button.text(chat.type == "searched" || chat.type == "roulette" ? "Search again" : "Join");
				if (chat.type == "searched" || chat.type == "roulette") { $("#send_form_wrap").addClass("abscond_again"); }
			}
			function disconnect() {
				exit();
				ws.close(1000);
				receive_messages({});
			}

			// Ping loop
			function ping() {
				if (status == "chatting" && ws.readyState == 1) {
					ws.send("ping");
					window.setTimeout(ping, 10000);
				}
			}

			// Quitting
			window.onbeforeunload = function(e) {
				if (status == "chatting" && user.meta.confirm_disconnect) {
					if (typeof e != "undefined") { e.preventDefault(); }
					return "";
				}
			}
			$(window).unload(function() {
				if (status == "chatting") {
					status = "disconnected";
				}
			});

			// Parsing and rendering messages
			var show_notification = false;
			function receive_messages(data) {
				if (typeof data.exit != "undefined") {
					exit();
					if (data.exit == "kick") {
						render_message({
							"acronym": "",
							"color": "000000",
							"id": null,
							"name": "",
							"posted": Math.floor(Date.now() / 1000),
							"text": "You have been kicked from this chat. Please think long and hard about your behavior before returning.",
							"type": "exit",
							"user_number": null,
						});
						scroll_to_bottom();
					} else if (data.exit == "ban") {
						if (chat.url != "theoubliette") { location.replace("/theoubliette") };
					}
					return;
				}
				if (typeof data.chat != "undefined" && chat.type != "pm") {
					chat = data.chat;
					if (chat.type == "group") {
						topic.text(chat.topic);
						if (user.meta.show_bbcode) {
							description.html(bbencode(chat.description, false));
							rules.html(bbencode(chat.rules, false));
						} else {
							description.text(bbremove(chat.description));
							rules.text(bbremove(chat.rules));
						}
						flag_autosilence.prop("checked", chat.autosilence);
						if (chat.publicity == "pinned" && user.meta.group != "admin") {
							flag_publicity.val("listed");
							flag_publicity.prop("disabled", true);
						} else {
							flag_publicity.val(chat.publicity);
							flag_publicity.prop("disabled", false);
						}
						chat.publicity == "private" ? invites_link.show() : invites_link.hide();
						flag_style.val(chat.style);
						flag_level.val(chat.level);
						chat.autosilence ? flag_message_autosilence.show() : flag_message_autosilence.hide();
						chat.publicity == "listed" || chat.publicity == "pinned" ? flag_message_publicity.show() : flag_message_publicity.hide();
						flag_message_style.html(style_messages[chat.style]);
						flag_message_level.html(level_names[chat.level]);
					}
				}
				if (typeof data.users != "undefined") {
					var others_online = false;
					for (var i = 0; i < data.users.length; i++) {
						// Store user data so we can look it up for action lists.
						user_data[data.users[i].meta.number] = data.users[i];
						// Also handle group changes.
						if (data.users[i].meta.number == user.meta.number) {
							user.meta.group = data.users[i].meta.group;
							if (chat.type == "group") {
								if (user.meta.group == "admin" || user.meta.group == "creator" || user.meta.group == "mod3" || user.meta.group == "mod2" || user.meta.group == "mod1") {
									mod_tools.show();
									info_panel_controls.show();
									flag_messages.hide();
								} else {
									mod_tools.hide();
									info_panel_controls.hide();
									flag_messages.show();
								}
							}
							if (user.meta.group == "silent") {
								text_input.prop("disabled", true);
								send_button.prop("disabled", true);
							} else {
								text_input.prop("disabled", false);
								send_button.prop("disabled", false);
							}
						} else {
							others_online = true;
						}
					}
					if (chat.type == "pm" || chat.type == "roulette") {
						var status_message = (chat.type == "pm" ? chat.url.substr(3) : "▼") + " is " + (others_online ? "online." : "offline.");
						if (previous_status_message) {
							previous_status_message = status_message;
						} else {
							status_bar.text(status_message);
						}
					} else {
						user_list.html(user_list_template(data));
						user_list.find("li").click(render_action_list);
						$("#conversation_wrap").off();
						$("#conversation_wrap").on("click", ".unum:not(.cnum_noclick)", render_action_list);
						// Re-render the action list if necessary.
						if (action_user != null) {
							var action_user_number = action_user.meta.number;
							var action_user_li = user_list.find("#unum_" + action_user_number);
							// Set to null so it fires the open action rather than the close action.
							if (action_user_li.length != 0) {
								action_user = null;
								action_user_li.click();
							}
						}
					}
				}
				if (typeof data.messages != "undefined" && data.messages.length != 0) {
					var scroll_after_render = is_at_bottom();
					data.messages.forEach(render_message);
					if (scroll_after_render) { scroll_to_bottom(); }
				}
				if (typeof data.delete != "undefined" && data.delete.length != 0) {
					data.delete.forEach(function(id) {
						console.log("delete " + id);
						$("#message_" + id).remove();
						// Remove "New messages" text if this was the only message.
						if (new_messages.length > 0) {
							var index = new_messages.indexOf(id);
							if (index != -1) { new_messages.splice(index, 1); }
							if (new_messages.length == 0) { document.title = original_title; }
						}
					});
				}
				if (typeof data.typing != "undefined") {
					if (!user.meta.typing_notifications && chat.type !== "pm" && chat.type !== "roulette") {
						status_bar.css("display", "none");
					} else {
						status_bar.css("display", "block");
					}
					if (data.typing.length == 0 || (data.typing.length == 1 && data.typing.indexOf(user.meta.number) == 0)) {
						if (previous_status_message) {
							status_bar.text(previous_status_message);
							previous_status_message = null;
						}
						$("#activity_spinner").removeClass("active_sb");
						$("#activity_spinner").attr("title", "No activity");
					} else {
						if (!previous_status_message) { previous_status_message = status_bar.text(); }
						var name = chat.type == "pm" ? chat.url.substr(3) : chat.type == "roulette" ? "▼" : "Someone";
						status_bar.text(name + " is typing...");
						$("#activity_spinner").addClass("active_sb");
						$("#activity_spinner").attr("title", "Someone is typing...");
					}
				}
				if (chat.type == "pm" && typeof data.pm != "undefined") {
					refresh_pm_chat_list();
				}
				if (status == "disconnected") {
					if (next_chat_url) {
						$.get("/" + next_chat_url + ".json", {}, function(data) {
							chat = data.chat;
							document.title = chat.title + " - MSPARP";
							history.replaceState({}, chat.url, "/" + chat.url);
							user = data.chat_user;
							latest_message_id = data.latest_message_id;
							conversation.html("<p><a href=\"/" + chat.url + "/log\" target=\"_blank\">View log</a></p>");
							status_bar = $("<p>").attr("id", "status_bar").appendTo(conversation);
							data.messages.forEach(render_message);
							connect();
						});
						next_chat_url = null;
					} else {
						$("#disconnect_links").appendTo(conversation);
						if (user.meta.subscribed) {
							$(".disconnect_subscribe").css("display", "none");
							$(".disconnect_subscribed").css("display", "inline");
						} else {
							$(".disconnect_subscribe").css("display", "inline");
							$(".disconnect_subscribed").css("display", "none");
						}
						scroll_to_bottom();
					}
				}
			}
			function render_message(message) {
				// XXX yeah you should be using a template here
				// Use initial setting for consistency.
				if (latest_date) {
					if (typeof message.posted == "number") { message.posted = message.posted * 1000 }
					message_date = new Date(message.posted);
					if (latest_date.getDate() != message_date.getDate() || latest_date.getMonth() != message_date.getMonth() || latest_date.getFullYear() != message_date.getFullYear()) {
						$("<h2>").text(message_date.toDateString()).insertBefore(status_bar);
					}
					latest_date = message_date;
				}
				var div = $("<div>");
				if (message.id) {
					latest_message_id = message.id;
					div.attr("id", "message_" + message.id);
				}
				div.addClass("message_" + message.type + " unum_" + message.user_number);
				$("<div>").attr("tabindex", -1).addClass("unum cnum_" + (message.user_number ? message.user_number + (message.user_number >= 1000 ? " four_digit" : "") + (message.user_number >= 10000 ? " five_digit" : "") : "noclick")).html((message.user_number ? "<span class=\"unum_hash\">#</span>" + message.user_number : "<span class=\"unum_system\">*</span>") ).appendTo(div);
				var p = $("<p>").css("color", "#" + message.color);
				if (message.type == "me") {
					var text = "* " + message.name + " " + message.text;
				} else if (chat.type == "roulette" && ["ic", "ooc"].indexOf(message.type) != -1) {
					var text = (message.user_number == user.meta.number ? "▲" : "▼") + ": " + message.text;
				} else if (message.acronym != "") {
					var text = message.acronym + ": " + message.text;
				} else {
					var text = message.text;
				}
				var admin = (message.user_number && user_data[message.user_number] && user_data[message.user_number].meta.group == "admin");
				user.meta.show_bbcode ? p.html(bbencode(text, admin)) : p.text(bbremove(text));
				if (chat.type == "searched" && (message.type == "disconnect" || message.type == "timeout") && message.user_number != user.meta.number) {
					$("<a>").attr("href", "#").addClass("message_action").text("Block").click(function() { block(message.user_number); return false; }).appendTo(p);
				} else if (message.type == "user_group" && ranks[user.meta.group] >= ranks["mod3"] && user_data[message.user_number] && user_data[message.user_number].meta.group == "silent") {
					$("<a>").attr("href", "#").addClass("message_action").text("Unsilence").click(function() {
						if (user_data[message.user_number].meta.group == "silent") { set_group(message.user_number, "user"); }
						return false;
					}).appendTo(p);
				} else if (message.type == "user_action" && ranks[user.meta.group] >= ranks["mod3"] && message.text.indexOf("] banned ") != -1) {
					$("<a>").attr("href", "#").addClass("message_action").text("Unban").click(function() {
						$.post("/" + chat.url + "/unban", {"number": message.user_number});
						return false;
					}).appendTo(p);
				} else if (message.type == "username_request") {
					$("<a>").attr("href", "#").addClass("message_action").text("Allow").click(function() {
						$.post("/chat_api/exchange_usernames", {"chat_id": chat.id, "number": message.user_number});
						$(this.parentNode.parentNode).remove();
						return false;
					}).appendTo(p);
					$("<a>").attr("href", "#").addClass("message_action").text("Deny").click(function() {
						$(this.parentNode.parentNode).remove();
						return false;
					}).appendTo(p);
				}
				if (latest_date) {
					$("<time>").addClass("timestamp").text(message_date.toLocaleTimeString()).appendTo(p);
				}
				p.appendTo(div);
				if (message.user_number && user.meta.highlighted_numbers.indexOf(message.user_number) != -1) { div.addClass("highlighted"); }
				if (message.user_number && user.meta.ignored_numbers.indexOf(message.user_number) != -1) { div.addClass("ignored"); }
				div.insertBefore(status_bar);
				
				// Limit conversation length on mobile to cycle 200 messages so as to not kill touch responsiveness
				if (touch_enabled) {
					var cycle = $('#conversation').find("div[id^=message]:nth-last-child(n+200)");
					cycle.prevAll("h2").remove(); // remove date stamps as well
					cycle.remove();
				}
				
				// Post all global messages as a notification banner.
				if (message.type.indexOf("global") !== -1 && message.important) {
					announcement_banner(message.title, message.text, message.headercolor);
				}

				if (
					(document.hidden || document.webkitHidden || document.msHidden)
					// Skip notifications for system messages if we're hiding them.
					&& (user.meta.show_system_messages || ["ic", "ooc", "me", "global", "spamless"].indexOf(message.type) != -1)
					// Skip notifications if we're ignoring this person.
					&& user.meta.ignored_numbers.indexOf(message.user_number) == -1
				) {
					new_messages.push(message.id);
					document.title = "New message - " + original_title;
					if (user.meta.desktop_notifications && typeof Notification != "undefined") {
						var text_without_bbcode = text.replace(/\[spoiler\]([\s\S]*?)\[\/spoiler\]/ig, "[SPOILER]");
						text_without_bbcode = bbremove(text_without_bbcode);
						// make this optional so notifications don't error on mobile when they've been enabled on another device
						try {
							var notification = new Notification(chat.title || "MSPARP", {
								"body": text_without_bbcode.length <= 50 ? text_without_bbcode : text_without_bbcode.substr(0, 47) + "...",
								"icon": "/static/img/spinner-big.png"
							});

							notification.onclick = function() {
								window.focus();
								this.close();
							}

							window.setTimeout(notification.close.bind(notification), 5000);
						} catch (e) { }
					}
				}
			}

			// "New message" notification
			var original_title = document.title;
			function visibility_handler() {
				window.setTimeout(function() { new_messages = []; document.title = original_title; }, 200);
			}
			if (typeof document.hidden !== "undefined") {
				document.addEventListener("visibilitychange", visibility_handler);
			} else if (typeof document.msHidden !== "undefined") {
				document.addEventListener("msvisibilitychange", visibility_handler);
			} else if (typeof document.webkitHidden !== "undefined") {
				document.addEventListener("webkitvisibilitychange", visibility_handler);
			}

			// Names and text
			var style_messages = {
				"script": "Please use <span class=\"flag_label\">script style</span>.",
				"paragraph": "Please use <span class=\"flag_label\">paragraph style</span>.",
				"either": "<span class=\"flag_label\">Script</span> and <span class=\"flag_label\">paragraph style</span> are allowed.",
			};
			var level_names = { "sfw": "SFW", "nsfw": "NSFW", "nsfw-extreme": "NSFW extreme" };
			var group_descriptions = {
				"admin": "God tier moderator - MSPARP staff.",
				"creator": "Chat creator - can silence, kick and ban other users.",
				"mod3": "Professional Wet Blanket - can silence, kick and ban other users.",
				"mod2": "Bum's Rusher - can silence and kick other users.",
				"mod1": "Amateur Gavel-Slinger - can silence other users.",
				"user": "",
				"silent": "Silenced.",
			};

			// Actions and validation
			function can_block(their_number) {
				return (chat.type == "searched" || chat.type == "roulette") && their_number != user.meta.number;
			}
			function block(number) {
				text_input.val("/block " + number + " (reason)").focus();
			}
			function can_set_group(new_group, current_group) {
				// Setting group only works in group chats.
				if (chat.type != "group") { return false; }
				// Don't bother if they're already this group.
				if (ranks[new_group] == ranks[current_group]) { return false; }
				// You can't set groups at all if you're not a mod.
				if (ranks[user.meta.group] < 1) { return false; }
				// You can only set the group to one which is below yours.
				if (ranks[new_group] >= ranks[user.meta.group]) { return false; }
				// You can only set the group of people whose group is below yours.
				if (ranks[current_group] >= ranks[user.meta.group]) { return false; }
				return true;
			}
			function can_perform_action(action, their_group) {
				// User actions only work in group chats.
				if (chat.type != "group") { return false; }
				// You can only kick if you're a Bum's Rusher or above.
				if (action == "kick" && ranks[user.meta.group] < 2) { return false; }
				// You can only ban if you're a Bum's Rusher or above.
				if (action == "ban" && ranks[user.meta.group] < 3) { return false; }
				// You can only perform actions on people whose group is below yours.
				if (ranks[their_group] >= ranks[user.meta.group]) { return false; }
				return true;
			}
			if (chat.type == "group") {
				function set_group(number, group) { $.post("/chat_api/set_group", { "chat_id": chat.id, "number": number, "group": group }); }
				function user_action(number, action, reason) {
					var data = { "chat_id": chat.id, "number": number, "action": action };
					if (reason) { data["reason"] = reason; }
					$.post("/chat_api/user_action", data);
				}
			}

			// Text commands
			var text_commands = [
				{
					"regex": /^me (.*\S+.*)/,
					"chat_types": "all",
					"minimum_rank": 0,
					"description": function(match) {
						return "* " + user.character.name + " " + match[1];
					},
					"action": function(match) {
						$.post("/chat_api/send", { "chat_id": chat.id, "type": "me", "text": match[1] });
					},
				},
				{
					"regex": /^block (\d+)($|\s.*$)?/,
					"chat_types": "searched_and_roulette",
					"minimum_rank": 0,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || set_user.meta.number != user.meta.number) {
							if ((match[2] || "").trim().length > 500) { return "Block reasons can only be 500 characters long."; }
							return "Block " + name_from_user_number(parseInt(match[1])) + ". You will no longer encounter them in random chats.";
						} else {
							return "You can't block yourself.";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || set_user.meta.number != user.meta.number) {
							$.post("/chat_api/block", { "chat_id": chat.id, "number": match[1], "reason": (match[2] || "").trim() });
						}
					},
				},
				{
					"regex": /^username (\d+)$/,
					"chat_types": "all",
					"minimum_rank": 0,
					"description": function(match) {
						if (parseInt(match[1]) != user.meta.number) {
							return "Request " + name_from_user_number(parseInt(match[1])) + "'s username.";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (set_user && set_user.meta.number != user.meta.number) {
							$.post("/chat_api/request_username", { "chat_id": chat.id, "number": match[1] });
						}
					},
				},
				{
					"regex": /^topic($|\s.*$)/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						var new_topic = match[1].trim();
						if (new_topic.length > 500) { return "Topics can only be 500 characters long."; }
						return new_topic ? "Set the topic to \"" + new_topic + "\"" : "Remove the topic.";
					},
					"action": function(match) {
						$.post("/chat_api/set_topic", { "chat_id": chat.id, "topic": match[1].trim() });
					},
				},
				{
					"regex": /^set (\d+) (mod3|mod2|mod1|user|silent)$/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						var group_description = group_descriptions[match[2]] || "regular user.";
						if (!set_user || can_set_group(match[2], set_user.meta.group)) {
							return "Set " + name_from_user_number(parseInt(match[1])) + " to " + group_descriptions[match[2]];
						} else if (match[2] == set_user.meta.group) {
							return set_user.character.name + " is already a member of this group.";
						} else {
							return "Your current privileges don't allow you to set " + set_user.character.name + "'s group.";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_set_group(match[2], set_user.meta.group)) { set_group(match[1], match[2]); }
					},
				},
				{
					"regex": /^kick (\d+)$/,
					"chat_types": "group",
					"minimum_rank": 2,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("kick", set_user.meta.group)) {
							return "Kick " + name_from_user_number(parseInt(match[1])) + " from the chat.";
						} else {
							return "Your current privileges don't allow you to kick " + set_user.character.name + ".";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("kick", set_user.meta.group)) { user_action(match[1], "kick"); }
					},
				},
				{
					"regex": /^ban (\d+)($|\s.*$)?/,
					"chat_types": "group",
					"minimum_rank": 3,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("ban", set_user.meta.group)) {
							if ((match[2] || "").trim().length > 500) { return "Ban reasons can only be 500 characters long."; }
							return "Ban " + name_from_user_number(parseInt(match[1])) + " from the chat.";
						} else {
							return "Your current privileges don't allow you to ban " + set_user.character.name + ".";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("ban", set_user.meta.group)) { user_action(match[1], "ban", (match[2] || "").trim()); }
					},
				},
				{
					"regex": /^unban (\d+)?/,
					"chat_types": "group",
					"minimum_rank": 3,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						return "Unban " + name_from_user_number(parseInt(match[1])) + " from the chat.";
					},
					"action": function(match) {
						$.post("/" + chat.url + "/unban", {"number": parseInt(match[1])});
					},
				},
				{
					"regex": /^autosilence (on|off)/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						return "Switch autosilence " + match[1] + ".";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "autosilence", "value": match[1] });
					},
				},
				{
					"regex": /^publicity (private|listed|unlisted)/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						return "Set the publicity to " + match[1] + ".";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "publicity", "value": match[1] });
					},
				},
				{
					"regex": /^publicity pinned/,
					"chat_types": "group",
					"minimum_rank": Infinity,
					"description": function(match) {
						return "Set the publicity to pinned.";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "publicity", "value": "pinned" });
					},
				},
				{
					"regex": /^level (sfw|nsfw|nsfw-extreme)$/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						return "Mark the chat as " + level_names[match[1]] + ".";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "level", "value": match[1] });
					},
				},
				{
					"regex": /^lookup (\d+)$/,
					"chat_types": "all",
					"minimum_rank": Infinity,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						return "Look up " + name_from_user_number(parseInt(match[1])) + ".";
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						$.post("/chat_api/look_up_user", { "chat_id": chat.id, "number": match[1] });
					},
				},
			];
			function name_from_user_number(number) {
				return user_data[number] ? user_data[number].character.name : "user " + number;
			}
			function get_command_description(text) {
				for (var i=0; i < text_commands.length; i++) {
					if (text_commands[i].chat_types == "group" && chat.type != "group") { continue; }
					if (text_commands[i].chat_types == "searched_and_roulette" && chat.type != "searched" && chat.type != "roulette") { continue; }
					if (text_commands[i].minimum_rank > ranks[user.meta.group]) { continue; }
					var match = text.match(text_commands[i].regex);
					if (match && match.length > 0) { return text_commands[i].description(match); }
				}
				return false;
			}
			function execute_command(text) {
				for (var i=0; i < text_commands.length; i++) {
					if (text_commands[i].chat_types == "group" && chat.type != "group") { continue; }
					if (text_commands[i].chat_types == "searched_and_roulette" && chat.type != "searched" && chat.type != "roulette") { continue; }
					if (text_commands[i].minimum_rank > ranks[user.meta.group]) { continue; }
					var match = text.match(text_commands[i].regex);
					if (match && match.length > 0) { text_commands[i].action(match); return true; }
				}
				return false;
			}

			// Temporary characters
			var temporary_character = null;
			function set_temporary_character(data) {
				temporary_character = data;
				text_preview.css("color", "#" + (data || user.character).color);
			}

			// Perform BBCode conversion
			$("#conversation div p").each(function(line) { user.meta.show_bbcode ? this.innerHTML = raw_bbencode(this.innerHTML, false) : $(this).html(bbremove(this.innerHTML)); });

			// Topbar and info panel
			if (chat.type == "group") {
				$("#topbar, #info_panel_link").click(function() {
					if (status != "chatting") { return false; }
					edit_info_panel.css("display") == "block" ? edit_info_panel.hide() : info_panel.toggle();
					$(".sidebar").removeClass("mobile_override");
					return false;
				});
				// There are several places where we show the topic, so we use this to update them all.
				var topic = $(".topic");
				var info_panel = $("#info_panel");
				var description = $(".description");
				var rules = $(".rules");
				var info_panel_controls = $(".info_panel_controls");
				$("#edit_info_button, #edit_info_link").click(function() {
					info_panel.hide();
					// Only set these when we need them.
					$("#edit_info_description").val(chat.description);
					$("#edit_info_rules").val(chat.rules);
					edit_info_panel.show();
				});
				$(".set_topic_button").click(function() {
					info_panel.hide();
					text_input.val("/topic ").focus();
				});
				var edit_info_panel = $("#edit_info_panel");
				$("#edit_info_form").submit(function() {
					var form_data = $(this).serializeArray();
					form_data.push({ name: "token", value: token });
					form_data.push({ name: "chat_id", value: chat.id });
					$.post("/chat_api/set_info", form_data);
					edit_info_panel.hide();
					return false;
				});
				$("#info_panel .close, #edit_info_panel .close").click(function() { info_panel.hide(); edit_info_panel.hide(); });
			}

			// PM chat list
			if (chat.type == "pm") {
				var pm_chat_list_container = $("#pm_chat_list_container");
				$("#pm_chat_list_container .close").click(function() { pm_chat_list_container.css("display", ""); });
				var pm_chat_list = $("#pm_chat_list");
				var pm_chat_list_template = Handlebars.compile($("#pm_chat_list_template").html());
				Handlebars.registerHelper("current_chat", function() {
					return this.chat.url == chat.url;
				});
				Handlebars.registerHelper("pm_username", function() { return this.chat.url.substr(3); });
				function refresh_pm_chat_list() {
					$.get("/chats/pm.json", {}, function(data) {
						pm_chat_list.html(pm_chat_list_template(data));
						var pm_chat_links = $("#pm_chat_list a").click(function() {
							// Hide PM chat list on mobile.
							if (pm_chat_list_container.css("display")) { pm_chat_list_container.css("display", ""); }
							var new_url = "pm" + this.href.substr(this.href.lastIndexOf("/"));
							if (chat.url == new_url) { return false; }
							next_chat_url = new_url;
							disconnect();
							pm_chat_links.removeClass("active");
							$(this).addClass("active");
							return false;
						});
					});
				}
			}

			// My Chats
			// currently saves filter preference to localStorage
			var my_chats = $("#my_chats");
			var my_chats_list = $("#my_chats_list");
			var my_chats_template = Handlebars.compile($("#my_chats_template").html());
			Handlebars.registerHelper("current_chat", function() {
				return this.chat.url == chat.url;
			});
			if (localstorage) {
				saved_type_filter = localStorage.getItem("type_filter_preference");
				if (saved_type_filter !== null) {$("#type_filter").val(saved_type_filter)}
			}
			function refresh_my_chats_list() {
				$.get("/chats.json", {}, function(data) {
					my_chats_list.html(my_chats_template(data));
				});
				$("#my_chats_list").removeClass();
				$("#my_chats_list").addClass("show_" + $("#type_filter").val());
			}
			
			// refresh list on opening
			$(".my_chats_button").click(function() { if (!$("#chat_wrapper").hasClass("my_chats_open")) { refresh_my_chats_list();} });
						
			// Filter My Chats
			$("#type_filter").change(function() {
				$("#my_chats_list").removeClass();
				$("#my_chats_list").addClass("show_" + $("#type_filter").val());
				if (localstorage) {
					localStorage.setItem("type_filter_preference", $("#type_filter").val());
				}
				refresh_my_chats_list();
			}); 
			
			// Sidebars
			var sidebars = $(".sidebar");
			// Set sidebar css trigger defaults, along with a list of closeable sidebar options so buttons can eliminate other open bars
			var sidebar_defaults = "";
			var sidebars_right = "";
			var sidebars_left = "";
			function reset_sidebar() {
				sidebar_defaults = "";
				sidebars_right = "";
				sidebars_left = "";
				if (status == "chatting" && chat.type == "group") {
					sidebar_defaults = "user_list_container_open side_info_open"; sidebars_right = "switch_character_open settings_open"; sidebars_left = "my_chats_open";
				} else if (status == "chatting" && chat.type == "searched") {
					sidebar_defaults = "user_list_container_open my_chats_only"; sidebars_right = "switch_character_open settings_open"; sidebars_left = "";
				} else if (status == "chatting" && chat.type == "roulette") {
					sidebar_defaults = "switch_character_open my_chats_only"; sidebars_right = "settings_open"; sidebars_left = "";
				} else if (status == "chatting" && chat.type == "pm") {
					sidebar_defaults = "switch_character_open pm_chat_list_container_open"; sidebars_right = "settings_open"; sidebars_left = "my_chats_open"
				}
				$(body).removeClass("has_left_tabs").removeClass("has_right_tabs");
				if (sidebars_left !== "") { $(body).addClass("has_left_tabs"); }
				if (sidebars_right !== "") { $(body).addClass("has_right_tabs"); }
				$("#chat_wrapper").removeClass();
				$("#chat_wrapper").addClass(sidebar_defaults);
				$(".sidebar").removeClass("mobile_override");
			}
			
			// Use the lists to close down other open bars, then hook individual buttons to open the desired one
			// Also close opposing bars if left sidebars are disabled or on msparp classic, or width is small enough to collapse left bars
			function open_sidebar(to_open) {
				if ($("#chat_wrapper").hasClass(to_open + "_open")) {
					$("#chat_wrapper").removeClass(to_open + "_open");
				} else {
					if (sidebars_right.indexOf(to_open) !=-1) {
						$("#chat_wrapper").removeClass(sidebars_right); 
						if ($('head link[href="/static/css/themes/msparp_basic.css"]').length || $('head link[href="/static/css/themes/msparp_basic_dark.css"]').length || $(body).hasClass("disable_left_bar") || window.innerWidth < 1270) {
							$("#chat_wrapper").removeClass(sidebars_left);
						}
					} else if (sidebars_left.indexOf(to_open) !=-1) {
						$("#chat_wrapper").removeClass(sidebars_left); 
						if ($('head link[href="/static/css/themes/msparp_basic.css"]').length || $('head link[href="/static/css/themes/msparp_basic_dark.css"]').length || $(body).hasClass("disable_left_bar") || window.innerWidth < 1270) {
							$("#chat_wrapper").removeClass(sidebars_right);
						}
					}
					$("#chat_wrapper").addClass(to_open + "_open"); 
				}
			}
			
			$(".switch_character_button").click(function() { open_sidebar("switch_character") });
			$(".settings_button").click(function() { open_sidebar("settings") });
			$(".my_chats_button").click(function() { open_sidebar("my_chats") });
			
			// Mobile side menu overrides
			 function mobile_sidebar(to_open) {
				$(".sidebar").not("#" + to_open).removeClass("mobile_override");
				$("#" + to_open).toggleClass("mobile_override");
				$("#mobile_nav_toggle").prop("checked",false);
			}
			
			$(".mobile_nav_button").click(function() { mobile_sidebar($(this).attr("id").replace("mobile_open_", "")) });
			
			// only close on non mobile if it isn't a default sidebar
			$(".sidebar .close").click(function() {if (sidebar_defaults.indexOf($(this).parents(".sidebar").attr("id")) == -1) {$("#chat_wrapper").removeClass($(this).parents(".sidebar").attr("id") + "_open") }; $(this).parents(".sidebar").removeClass("mobile_override"); });
			
			// Attempt to load smart quirk settings for this chat from localstorage, otherwise fall back to default
			var smart_quirk_mode = "";
			if (localstorage) {
				if (localStorage.getItem( chat.url + "_smart_quirk") !== null) {
					dev_user_smart_quirk = localStorage.getItem( chat.url + "_smart_quirk");
				}
				localStorage.setItem( chat.url + "_smart_quirk", dev_user_smart_quirk);
				dev_user_smart_quirk == "true" ? $("#chat_smart_quirk" + smart_quirk_mode).prop('checked',true) : $("#chat_smart_quirk" + smart_quirk_mode).prop('checked',false); 
				if (localStorage.getItem( chat.url + "_smart_quirk_mode") !== null) { 
					smart_quirk_mode = localStorage.getItem( chat.url + "_smart_quirk_mode"); 
					$("#smart_quirk_mode_" + smart_quirk_mode).prop('checked',true); 
				}
			}
			// If unset, base this on chat style, with script as fallback
			if (smart_quirk_mode == "") {
				smart_quirk_mode = "script"; $("#smart_quirk_mode_script").prop('checked',true);
				// check if group is paragraph
				if (chat.type == "group") {
					if (chat.style == "paragraph") {smart_quirk_mode = "paragraph"; $("#smart_quirk_mode_paragraph").prop('checked',true);}
				}
				if (chat.type == "searched") {
					// grab preference for searched chats, save it explicitly since style cannot be changed
					if ($(".message_search_info p").text().indexOf("This is a paragraph style chat.") != -1) {smart_quirk_mode = "paragraph"; $("#smart_quirk_mode_paragraph").prop('checked',true);}
					if (localstorage) {
						localStorage.setItem( chat.url + "_smart_quirk_mode", smart_quirk_mode);
					}
				}
			}
			
			// Update smart quirk settings and save for individual chats
			$("#settings #chat_smart_quirk").change(function() {
				if ($("#smart_quirk_mode_paragraph").prop('checked')) {
					// unset defaults to script, so reset value here
					smart_quirk_mode = "paragraph"
					if (localstorage) {
						localStorage.setItem( chat.url + "_smart_quirk_mode", smart_quirk_mode);
					}
				}
				if ($("#chat_smart_quirk").is(':checked')) {dev_user_smart_quirk = "true";}
				else { dev_user_smart_quirk = "false"; }
				if (localstorage) {
					localStorage.setItem( chat.url + "_smart_quirk", dev_user_smart_quirk);
				}
				$("#chat_line_input input").trigger( "keyup" ); // refresh text so the setting is more intuitive
			});
			
			$("#smart_quirk_select").change(function() {
				smart_quirk_mode = $('input[name=smart_quirk_mode]:checked').val();
				$("#chat_line_input input").trigger( "keyup" ); // refresh text so the setting is more intuitive
				if (localstorage) {
					localStorage.setItem( chat.url + "_smart_quirk_mode", smart_quirk_mode) 
				}
			}); 

			// Mod tools
			if (chat.type == "group") {
				var mod_tools = $("#mod_tools");
				var flag_autosilence = $("#flag_autosilence").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "autosilence", "value": this.checked ? "on" : "off" });
				});
				var flag_publicity = $("#flag_publicity").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "publicity", "value": this.value });
				});
				var invites_link = $("#invites_link");
				var flag_style = $("#flag_style").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "style", "value": this.value });
				});
				var flag_level = $("#flag_level").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "level", "value": this.value });
				});
				var flag_messages = $("#flag_messages");
				var flag_message_autosilence = $("#flag_message_autosilence");
				var flag_message_publicity = $("#flag_message_publicity");
				var flag_message_style = $("#flag_message_style");
				var flag_message_level = $("#flag_message_level");
			}

			// User list
			var user_list = $("#user_list");
			var user_list_template = Handlebars.compile($("#user_list_template").html());
			Handlebars.registerHelper("group_description", function(group) { return group_descriptions[group]; });
			Handlebars.registerHelper("is_you", function() { return this.meta.number == user.meta.number; });
			Handlebars.registerHelper("is_highlighted", function() { return user.meta.highlighted_numbers.indexOf(this.meta.number) != -1; });
			Handlebars.registerHelper("is_ignored", function() { return user.meta.ignored_numbers.indexOf(this.meta.number) != -1; });
			Handlebars.registerHelper("admin", function() { return user.meta.group == "admin"; });

			// Action list
			var action_user = null;
			var action_list = $("#action_list");
			var action_list_template = Handlebars.compile($("#action_list_template").html());
			var ranks = { "admin": Infinity, "creator": Infinity, "mod3": 3, "mod2": 2, "mod1": 1, "user": 0, "silent": -1 };
			function render_action_list(event) {
				var popup_pos = "top"
				var popup_x = 0;
				var popup_y = 0;
				if (this.id) {
					var action_user_number = parseInt(this.id.substr(5));
				} else {
					var action_user_number = parseInt(this.className.substr(10));
					if ((event.clientY / $( window ).height()) > .5) {popup_pos = "bottom"}
					popup_x = event.pageX;
					popup_y = event.pageY;
				}
				if (action_user && action_user_number == action_user.meta.number) {
					action_user = null;
					action_list.empty();
				} else {
					if (!user_data[action_user_number]) { return false }
					action_user = user_data[action_user_number];
					action_list.html(action_list_template(action_user));
					action_list.appendTo(this);
					action_list.removeClass().addClass(popup_pos);
					action_list.css("top", "");
					action_list.css("bottom", "");
					if (popup_pos == "top") {action_list.css("top", popup_y); }
					else {action_list.css("bottom", $( document ).height() - popup_y); }
					action_list.css("left", popup_x);
					$("#action_block").click(function() { block(action_user.meta.number); });
					$("#action_highlight").click(function() {
						if (user.meta.highlighted_numbers.indexOf(action_user.meta.number) != -1) {
							$(".unum_" + action_user.meta.number).removeClass("highlighted");
							user.meta.highlighted_numbers = user.meta.highlighted_numbers.filter(function(i) { return i != action_user.meta.number; })
						} else {
							$(".unum_" + action_user.meta.number).addClass("highlighted");
							user.meta.highlighted_numbers.push(action_user.meta.number);
						}
						$.post("/chat_api/save_variables", { "chat_id": chat.id, "highlighted_numbers": user.meta.highlighted_numbers.toString() });
					});
					$("#action_ignore").click(function() {
						if (user.meta.ignored_numbers.indexOf(action_user.meta.number) != -1) {
							$(".unum_" + action_user.meta.number).removeClass("ignored");
							user.meta.ignored_numbers = user.meta.ignored_numbers.filter(function(i) { return i != action_user.meta.number; })
						} else {
							$(".unum_" + action_user.meta.number).addClass("ignored");
							user.meta.ignored_numbers.push(action_user.meta.number);
						}
						$.post("/chat_api/save_variables", { "chat_id": chat.id, "ignored_numbers": user.meta.ignored_numbers.toString() });
					});
					$("#action_mobile_switch_character").click(function() {mobile_sidebar("switch_character") });
					$("#action_mobile_settings").click(function() {mobile_sidebar("settings") });
					$("#action_switch_character").click(function() { open_sidebar("switch_character") });
					$("#action_settings").click(function() { open_sidebar("settings") });
					$("#action_mod3, #action_mod2, #action_mod1, #action_user, #action_silent").click(function() {
						set_group(action_user.meta.number, this.id.substr(7));
					});
					$("#action_kick, #action_ban").click(function() {
						if (this.id == "action_ban") {
							var reason = prompt("Please provide a reason for this ban.");
							if (reason == null) { return; }
						}
						user_action(action_user.meta.number, this.id.substr(7), reason || "");
					});
					$("#action_request_username").click(function() {
						$.post("/chat_api/request_username", { "chat_id": chat.id, "number": action_user.meta.number });
					});
					$("#action_look_up_user").click(function() {
						$.post("/chat_api/look_up_user", { "chat_id": chat.id, "number": action_user.meta.number });
					});
				}
			}
			Handlebars.registerHelper("can_block", function(new_group) { return can_block(this.meta.number); });
			Handlebars.registerHelper("can_set_group", function(new_group) { return can_set_group(new_group, this.meta.group); });
			Handlebars.registerHelper("can_perform_action", function(action) { return can_perform_action(action, this.meta.group); });
			Handlebars.registerHelper("set_user_text", function() { return this.meta.group == "silent" ? "Unsilence" : "Unmod"; });

			// Switch character
			var switch_character = $("#switch_character");
			$("select[name=character_id]").change(function() {
				if (this.value != "") {
					$.get("/characters/"+this.value+".json", {}, update_character);
				}
			});
			initialize_character_form();
			$("#switch_character_form").submit(function() {
				if ($("input[name=name]").val().trim() == "") {
					alert("You can't chat with a blank name!");
				} else if ($("input[name=color]").val().match(/^#?[0-9a-fA-F]{6}$/) == null) {
					alert("You entered an invalid hex code.");
				} else {
					var form_data = $(this).serializeArray();
					form_data.push({ name: "token", value: token });
					form_data.push({ name: "chat_id", value: chat.id });
					$.post("/chat_api/save", form_data, function(data) {
						user = data;
						set_temporary_character(null);
						$("#chat_line_input input").trigger( "keyup" ); // refresh text line to apply new settings
					});
				}
				reset_sidebar();
				return false;
			});

			// Settings
			var settings = $("#settings");
			$(".variable").click(function() {
				var data = { "chat_id": chat.id };
				data[this.id] = this.checked ? "on" : "off";
				$.post("/chat_api/save_variables", data);
				user.meta[this.id] = this.checked;
				if (this.id == "desktop_notifications" && this.checked && typeof Notification != "undefined" && Notification.permission != "granted") {
					Notification.requestPermission();
				} else if (this.id == "typing_notifications") {
					if (chat.type == "pm" || chat.type == "roulette") {
						if (previous_status_message) {
							status_bar.text(previous_status_message);
							previous_status_message = null;
						}
					} else {
						status_bar.text(this.checked ? " " : "");
					}
				}
				parse_variables();
			});
			$("#desktop_notifications").prop("disabled", typeof Notification == "undefined");
			function parse_variables() {
				user.meta.show_preview ? text_preview.show() : text_preview.hide();
				user.meta.show_preview ? $("#send_form").removeClass("no_preview") : $("#send_form").addClass("no_preview") ;
				user.meta.show_system_messages ? conversation.removeClass("hide_system_messages") : conversation.addClass("hide_system_messages");
				user.meta.show_user_numbers ? conversation.removeClass("hide_user_numbers") : conversation.addClass("hide_user_numbers");
				user.meta.enable_activity_indicator ? $("#send_form").removeClass("disable_activity_indicator") : $("#send_form").addClass("disable_activity_indicator");
				resize_conversation();
			}
			$("#subscribed").click(function() {
				$.post("/" + chat.url + "/" + (this.checked ? "subscribe" : "unsubscribe"));
				user.meta.subscribed = this.checked;
			});
			$(".disconnect_subscribe").click(function() {
				$.post("/" + chat.url + "/" + ("subscribe"));
				user.meta.subscribed = true;
				$(".disconnect_subscribe").css("display", "none");
				$(".disconnect_subscribed").css("display", "inline");
				$('#subscribed').prop('checked', true);
			});
			$("#theme_form").submit(function() {
				var form_data = $(this).serializeArray();
				var new_theme = $(this).find("select").val();
				form_data.push({ name: "chat_id", value: chat.id });
				$.post(this.action, form_data, function() {
					var theme_stylesheet = $("#theme_stylesheet");
					if (new_theme) {
						var stylesheet_url = "/static/css/themes/" + new_theme + ".css";
						update_theme(new_theme);
						if (theme_stylesheet.length == 1) {
							theme_stylesheet.attr("href", stylesheet_url);
						} else {
							$("<link>").attr({id: "theme_stylesheet", rel: "stylesheet", href: stylesheet_url}).appendTo(document.head);
						}
					} else {
						theme_stylesheet.remove();
					}
				});
				reset_sidebar();
				return false;
			});

			// Conversation
			function is_at_bottom() {
				var current_scroll = conversation.scrollTop() + conversation.height();
				var max_scroll = conversation[0].scrollHeight;
				return max_scroll - current_scroll < 30;
			}
			function scroll_to_bottom() { conversation.scrollTop(conversation[0].scrollHeight); }
			function resize_conversation() {
				var scroll_after_resize = is_at_bottom();
				conversation.css("bottom", send_form.height() + 10 + "px");
				if (scroll_after_resize) { scroll_to_bottom(); }
			}
			var status_bar = $("#status_bar");
			var previous_status_message;

			// Send form
			var typing;
			var typing_timeout;
			var text_preview = $("#text_preview");
			function set_text_preview(text) {
				text_preview.html(bbencode(text.substring(0, 10000))); // XXX Find a way to link this with the Message.MAX_LENGTH constant.
				resize_conversation();
			}

			var changed_since_draft = false;
			window.setInterval(function() {
				if (changed_since_draft) {
					console.log("changed");
					$.post("/chat_api/draft", { "chat_id": chat.id, "text": text_input.val().trim() });
				}
				changed_since_draft = false;
			}, 15000);

			var text_input = $("input[name=text]").keydown(function() {
				changed_since_draft = true;
				window.clearTimeout(typing_timeout);
				if (!typing) {
					typing = true;
					ws.send("typing");
					$("#activity_spinner").addClass("active_self");
					$("#activity_spinner").attr("title", "You are typing...");
				}
				typing_timeout = window.setTimeout(function() {
					typing = false;
					ws.send("stopped_typing");
					$("#activity_spinner").removeClass("active_self");
					$("#activity_spinner").attr("title", "No activity");
				}, 1000);
			}).keyup(function() {
				if (user.meta.show_preview) {
					text = this.value.trim()
					if (text[0] == "/") {
						var text = text.substr(1);
						var command_description = get_command_description(text);
						// Look up a saved character.
						if (!command_description) {
							// Skip all this if it's the same character as last time.
							if (temporary_character && text.lastIndexOf(temporary_character.shortcut + " ", 0) == 0) {
								set_text_preview(apply_quirks(text.substr(temporary_character.shortcut.length + 1)));
								return;
							}
							for (var shortcut in character_shortcuts) {
								if (text.lastIndexOf(shortcut + " ", 0) == 0) {
									$.get("/characters/" + character_shortcuts[shortcut] + ".json", {}, function(data) {
										set_temporary_character(data);
										set_text_preview(apply_quirks(text.substr(shortcut.length + 1)));
									}).error(function() {
										set_temporary_character(null);
										delete character_shortcuts[shortcut];
										text_input.keyup();
									});
									return;
								}
							}
						}
						set_text_preview(command_description || text);
					} else if (text.substr(0, 7) == "http://" || text.substr(0, 8) == "https://" || ["((", "[[", "{{"].indexOf(text.substr(0, 2)) != -1) {
						set_text_preview(text);
					} else {
						set_text_preview(apply_quirks(text));
					}
					// Clear the temporary character if necessary.
					if (temporary_character) { set_temporary_character(null); }
				}
			});
			var send_form = $("#send_form").submit(function() {
				var data = { "chat_id": chat.id, "text": text_input.val().trim(), "type": "ic" };
				if (data.text == "") { return false; }
				if (data.text[0] == "/") {
					data.text = data.text.substr(1);
					// Try to parse the text as a command, and skip the rest if we can.
					var executed = execute_command(data.text);
					if (executed) {
						text_input.val("");
						typing = false;
						ws.send("stopped_typing");
						return false;
					}
					// If the current temporary character matches, apply their quirks.
					if (temporary_character && data.text.lastIndexOf(temporary_character.shortcut + " ", 0) == 0) {
						data.text = apply_quirks(data.text.substr(temporary_character.shortcut.length + 1)).trim();
						data.character_id = temporary_character.id;
					} else {
						// If not, look up another saved character.
						for (var shortcut in character_shortcuts) {
							if (data.text.lastIndexOf(shortcut + " ", 0) == 0) {
								$.get("/characters/" + character_shortcuts[shortcut] + ".json", {}, function(data) {
									set_temporary_character(data);
									send_form.submit();
								}).error(function() {
									set_temporary_character(null);
									delete character_shortcuts[shortcut];
									send_form.submit();
								});
								return false;
							}
						}
						// If that doesn't work, make sure the temporary character is cleared.
						if (temporary_character) { set_temporary_character(null); }
					}
				} else if (data.text.substr(0, 7) == "http://" || data.text.substr(0, 8) == "https://") {
					// Don't apply quirks if the message starts with a link.
				} else if (["((", "[[", "{{"].indexOf(data.text.substr(0, 2)) != -1) {
					// Don't apply quirks to OOC messages
					data.type = "ooc";
				} else {
					data.text = apply_quirks(data.text).trim();
				}
				// Check if it's blank before and after because quirks may make it blank.
				if (data.text == "") { return false; }
				$.post("/chat_api/send", data);
				text_input.val("");
				last_alternating_line = !last_alternating_line;
				if (temporary_character) { set_temporary_character(null); }
				changed_since_draft = false;
				typing = false;
				return false;
			});
			var send_button = send_form.find("button[type=submit]");

			// Text entry keyboard shortcuts
			var ctrl_command = false;
			var alt_command = false;
			function insert_bbcode(target, initial, closing, is_attribute) {
				var len = target.val().length;
				var start = target[0].selectionStart;
				var end = target[0].selectionEnd;
				var selection = target.val().substring(start, end);
				var output = initial + selection + closing;
				target.val(target.val().substring(0, start) + output + target.val().substring(end, len));
				// if selection is empty, place caret within new tag
				if (selection.length == 0 && is_attribute == false) {
					target[0].selectionStart = start + initial.length;
					target[0].selectionEnd = start + initial.length;
				}
				// if we're inserting a tag with an attribute value, place cursor at hex/value position
				if (is_attribute == true) {
					target[0].selectionStart = start + initial.length - 1;
					target[0].selectionEnd = start + initial.length - 1;
				}
				ctrl_command = false;
				alt_command = false;
			}
			
			// Shortcut listener check; ctrl = 17; osx command = 91 (Safari), 224 (FF)			
			function is_shortcut(e) {
				var target = e.target || e.srcElement;
				target = $(target); // pass target as jQuery
				var keyLocation = ["Standard", "Left", "Right", "Numpad", "Mobile", "Joystick"][e.location];
				if (e.keyCode == 18 && keyLocation !== "Right") alt_command=true;
				if (e.keyCode == 17 || e.keyCode == 91 || e.keyCode == 224) ctrl_command=true;
				if (ctrl_command == true && alt_command == true){
					switch (e.keyCode) {
						case 13: // enter for br/newline
							insert_bbcode(target, "[br]", "", false);
							return true;
						case 74: // j for sup
						case 38: // up arrow for sup
							insert_bbcode(target, "[sup]", "[/sup]", false);
							return true;
						case 75: // k for sub
						case 40: // down arrow for sub
							insert_bbcode(target, "[sub]", "[/sub]", false);
							return true;
						case 66: // b for bold
							insert_bbcode(target, "[b]", "[/b]", false);
							return true;
						case 67: // c for caps
							insert_bbcode(target, "[c]", "[/c]", false);
							return true;
						case 70: // f for font 
							insert_bbcode(target, "[font=]", "[/font]", true);
							return true;
						case 71: // g for bgcolor (since b is taken)
							insert_bbcode(target, "[bgcolor=]", "[/bgcolor]", true);
							return true;
						case 72: // h for hex (since c is needed)
							insert_bbcode(target, "[color=]", "[/color]", true);
							return true;
						case 73: // i for italics
							insert_bbcode(target, "[i]", "[/i]", false);
							return true;
						case 76: // l for aLternian (since a is needed)
							insert_bbcode(target, "[alternian]", "[/alternian]", false);
							return true;
						case 79: // o for open/link (since u is underline)
							insert_bbcode(target, "[url=]", "[/url]", true);
							return true;
						case 80: // p for sPoiler (since s is strikethrough)
							insert_bbcode(target, "[spoiler]", "[/spoiler]", false);
							return true;
						case 82: // r for raw
							insert_bbcode(target, "[raw]", "[/raw]", false);
							return true;
						case 83: // s for strikethrough
							insert_bbcode(target, "[s]", "[/s]", false);
							return true;
						case 85: // u for underline
							insert_bbcode(target, "[u]", "[/u]", false);
							return true;
						case 87: // w for whisper
							insert_bbcode(target, "[w]", "[/w]", false);
							return true;
						case 190: // toggle preview on/off with "."
							$("#show_preview").click();
							return true;
					}
				}
				return false;
			}
			
			// Attach functions only where needed (if not disabled) so other shortcuts work normally if not focussed
			if (chat.type == "group") { var shortcut_enabled = ["chat_line_input", "edit_info_description", "edit_info_rules"]; }
			else { var shortcut_enabled = ["chat_line_input"]; }
			if (dev_user_disable_hotkeys !== "true") {
				for (i = 0; i < shortcut_enabled.length; i++) {
					document.getElementById(shortcut_enabled[i]).addEventListener("keyup", function(e) {
						alt_command = false;
						ctrl_command = false;
					});
					document.getElementById(shortcut_enabled[i]).addEventListener("keydown", function(e) {
						// prevent default if we're actually using a shortcut
						if (is_shortcut(e)) {
							e.preventDefault();
							return false;
						}
					});
				}
			}
			
			// Typing quirks
			var last_alternating_line = false;

			function apply_quirks(text) {
				var character = (temporary_character || user.character);
				
				if (dev_user_safe_bbcode == "true") {
					// as they are case sensitive, save URLs to array to survive this step
					var url_matches = text.match(/\[url=([^\]]+?)\]/gi);
					// save [raw] content so quirks don't apply to it at all; greedy so [raw] inside [raw] works
					var re = /\[raw\](.*)\[\/raw\]/gi;
					var raw_content = false;
					if (match = re.exec(text)) {
						raw_content = match[1];
					}
					text = text.replace(re, "\ufe5drawc\ufe5e");
					// selectively replace [BBCode] tag wrapping with unicode placeholders to do negative lookaheads without e.g. Terezi's quirk breaking
					// to be consistent, use same rules here that are used for BBCode removal, except recursive to catch stacked tags
					var re = /\[([A-Za-z]+)(=[^\]]+)?\]([\s\S]*?)\[(\/\1)\]/ig;
					while (re.exec(text)) {
						text = text.replace(re, "\ufe5d$1$2\ufe5e$3\ufe5d$4\ufe5e");
					}
					// also wrap [br] tags
					text = text.replace(/\[([bB][rR])\]/g, "\ufe5d$1\ufe5e");
				}
				
				// Break up text into chunks for smartquirking
				var text_chunks = new Array();
				
				if (dev_user_smart_quirk == "true") {
					if (smart_quirk_mode == "paragraph") { text_chunks = text.split(dev_user_smart_dialogue_delimiter); }
					if (smart_quirk_mode == "script") { text_chunks = text.split(dev_user_smart_action_delimiter); }
				} else {
					text_chunks[0] = text;
					smart_quirk_mode = "script";
				}
				
				var final_text = "";
				var chunks_number = text_chunks.length;
				for (var i = 0; i < chunks_number; i++) {
					// Apply case and quirk only between appropriate delimiters
					if ((i % 2 == 0 &&  smart_quirk_mode == "script") || (i % 2 !== 0 &&  smart_quirk_mode == "paragraph")) {
						// Case options.
						// ["case"] instead of .case because .case breaks some phones and stuff.
						switch (character["case"]) {
							case "lower":
								// Adaptive lower
								// Part 1: convert words to lower case if they have at least one lower case letter in them.
								text_chunks[i] = text_chunks[i].replace(/\w*[a-z]+\w*/g, function(str) { return str.toLowerCase(); });
								// Part 2: convert lone capital letters (eg. I) to lower case.
								// Find single capital letters with adjacent lower case ones, potentially looping in case they overlap.
								text_chunks[i] = text_chunks[i].replace(/(^|[a-z])(\W*[A-Z]\W*([a-z]|$))+/g, function(str) { return str.toLowerCase(); });
								// Part 3: also catch I... I [...], or other punctuation cases.
								text_chunks[i] = text_chunks[i].replace(/(^|[a-z])(\W*I[\W.,!?]*I\W*([a-z]|$))+/g, function(str) { return str.toLowerCase(); });
								break;
							case "upper":
								text_chunks[i] = text_chunks[i].toUpperCase();
								break;
							case "title":
								// Capitalise the first letter at the beginning, and after a word break if it's not an apostrophe.
								text_chunks[i] = text_chunks[i].toLowerCase().replace(/(^|[^']\b)\w/g, function(str) { return str.toUpperCase(); });
								break;
							case "inverted":
								// Lower case the first letter at the beginning, the first letter of each sentence, and lone Is.
								text_chunks[i] = text_chunks[i].toUpperCase().replace(/^.|[,.?!]\s+\w|\bI\b/g, function(str){ return str.toLowerCase(); });
								break;
							case "alternating":
								// Pick up pairs of letters (optionally with whitespace in between) and capitalise the first in each pair.
								text_chunks[i] = text_chunks[i].toLowerCase().replace(/(\w)\W*\w?/g, function(str, p1){ return str.replace(p1, p1.toUpperCase()); });
								break;
							case "alt-lines":
								text_chunks[i] = last_alternating_line ? text_chunks[i].toUpperCase() : text_chunks[i].toLowerCase();
								break;
							case "proper":
								// Capitalise the first letter at the beginning, the first letter of each sentence, and lone Is.
								text_chunks[i] = text_chunks[i].replace(/(^|[^.][.?!]\s+)(\w)/g, function(str, p1, p2){ return p1 + p2.toUpperCase(); });
								text_chunks[i] = text_chunks[i].replace(/\bi\b/g, "I");
								break;
							case "first-letter":
								// Part 1: same as adaptive lower.
								text_chunks[i] = text_chunks[i].replace(/\w*[a-z]+\w*/g, function(str) { return str.toLowerCase(); });
								text_chunks[i] = text_chunks[i].replace(/(^|[a-z])(\W*[A-Z]\W*([a-z]|$))+/g, function(str) { return str.toLowerCase(); });
								// Part 2: capitalise the first letter at the beginning and the first letter of each sentence.
								text_chunks[i] = text_chunks[i].replace(/(^|[^.][.?!]\s+)(\w)/g, function(str, p1, p2){ return p1 + p2.toUpperCase(); });
								break;
						}
						// Ordinary replacements. Escape any regex control characters before replacing.
						character.replacements.forEach(function(replacement) {
							RegExp.quote = function(str) {return str.replace(/([.?*+^$[\]\\(){}|-])/g, "\\$1"); }
							if (dev_user_safe_bbcode == "true") { 
								// if safe_bbcode is on, exclude quirking within custom [brackets]
								var re = new RegExp("(?![^\ufe5d\ufe5e]*\ufe5e)" + RegExp.quote(replacement[0]) + "(?![^\ufe5d\ufe5e]*\ufe5e)", "g");
							} else {
								var re = new RegExp(RegExp.quote(replacement[0]), "g");
							}
							text_chunks[i] = text_chunks[i].replace(re, replacement[1]);
						});
						// Regex replacements
						character.regexes.forEach(function(replacement) {
							try {
								if (dev_user_safe_bbcode == "true") { 
									// if safe_bbcode is on, exclude quirking within custom [brackets]
									var re = new RegExp("(?![^\ufe5d\ufe5e]*\ufe5e)" + replacement[0] + "(?![^\ufe5d\ufe5e]*\ufe5e)", "g");
								} else {
									var re = new RegExp(replacement[0], "g");
								}
								// allow regex quirks to case matched element via $U and $L
								if (replacement[1] == "$U") {
									text_chunks[i] = text_chunks[i].replace(re, function(str) { return str.toUpperCase(); });
								} else if (replacement[1] == "$L") {
									text_chunks[i] = text_chunks[i].replace(re, function(str) { return str.toLowerCase(); });
								} else {
									text_chunks[i] = text_chunks[i].replace(re, replacement[1]);
								}
							} catch (e) {
								text_chunks[i] = "A young person stands in their bedroom. They don't know Regexp.";
								return;
							}
						});
						// Prefix and suffix, add in delimiter for quirked paragraph text, respect smart quirk wrap setting
						if (smart_quirk_mode == "paragraph" && text_chunks[i] != "") {
							if (dev_user_wrap_smart_quirks == "true") {
								final_text = final_text + dev_user_smart_dialogue_delimiter + character.quirk_prefix + text_chunks[i] + character.quirk_suffix + dev_user_smart_dialogue_delimiter;
							} else {
								final_text = final_text + dev_user_smart_dialogue_delimiter + text_chunks[i] + dev_user_smart_dialogue_delimiter;
							}
						}
						if (smart_quirk_mode == "script" && text_chunks[i] != "") {
							// strip whitespace if present to allow normal action delimiter spacing
							if (dev_user_wrap_smart_quirks == "true") {
								final_text = final_text + character.quirk_prefix + text_chunks[i].replace(/^\s|\s$/,"") + character.quirk_suffix;
							} else {
								final_text = final_text + text_chunks[i].replace(/^\s|\s$/,"");
							}
						}
					} else {
						// If quirking should not apply, add the plain text; add in delimiter for unquirked script text
						if (smart_quirk_mode == "script" && text_chunks[i] != "") { final_text = final_text + " " + dev_user_smart_action_delimiter + text_chunks[i] + dev_user_smart_action_delimiter + " "; }
						else { final_text = final_text + text_chunks[i]; }
					}
				}
				// add in prefix and suffix if it should be global
				if (dev_user_wrap_smart_quirks !== "true") { final_text = character.quirk_prefix + final_text + character.quirk_suffix }
				
				if (dev_user_safe_bbcode == "true") {
					// now that we are safe, replace temporary unicode brackets with coding ones again
					final_text = final_text.replace(/\ufe5d/g, "[").replace(/\ufe5e/g,"]");
					
					// begin by removing empty tags
					var re2 = /\[([A-Za-z]+)(=[^\]]+)?\](\s+)?\[\/\1\]/ig;
					final_text = final_text.replace(re2, "$3");
					// only get more involved if we have nested/potentially problematic tags, from quirks or otherwise
					if (/\[[^\/\]]+\][^\[\]]*?\[[^\/\]]+\]/.test(final_text)) {
						// attempt to catch improperly stacked colour, bgcolor and font tags  
						var re = /(\[(color|bgcolor|font)=([#\w\d\s'-.,()]+)\])(([\s\S](?!\[\/\2\]))*?)(\[\2=[#\w\d\s'-.,()]+\])([\s\S]*?)(\[\/\2\])/i;
						while (re.test(final_text)) {
							// close and reopen tags
							final_text = final_text.replace(re, "$1$4[/$2]$6$7$8[$2=$3]");
							// strip empty tags
							final_text = final_text.replace(re2, "$3");
						}
						// escape [br]s and [rawc] again for this step so they aren't picked up as non matching
						final_text = final_text.replace(/\[(br|rawc)\]/gi, "\ufe5d$1\ufe5e");
						// fix intersecting tags
						var re = /(\[([A-Za-z]+)(=[^\]]+)?\])(([\s\S](?!\[\/\2\]))*?)\[([A-Za-z]+)(=[^\]]+)?\](([\s\S](?!\[\/\6\]))*?)(\[\/\2\])(.*?)(\[\/\6\])/i;
						var panic = 0;
						while (match = re.exec(final_text)) {
							// strip empty tags
							final_text = final_text.replace(re2, "$3");
							panic++
							if (match[4].indexOf(match[1]) !== -1) {
								// strip empty tags
								final_text = final_text.replace(re2, "$3");
								console.log("BREAK: Stacking cannot be recovered.");
								break;
							} else if (panic > 50) {
								// strip empty tags
								final_text = final_text.replace(re2, "$3");
								console.log("BREAK: Too many BBCode intersection issues.");
								break;
							}
							// close and reopen tags
							final_text = final_text.replace(re, "$1$4[$6$7]$8[/$6]$10[$6$7]$11$12" ); 
							// strip empty tags
							final_text = final_text.replace(re2, "$3");
						}
						// make [br]s coding again
						final_text = final_text.replace(/\ufe5d/g, "[").replace(/\ufe5e/g,"]");
					}
					// reinsert original [raw] content
					if (raw_content !== false) {
						final_text = final_text.replace(/\[rawc\]/i, "[raw]" + raw_content + "[/raw]");
					}
					// this is also where we replace URLs with original casing
					if (url_matches !== null) {
						var urls_number = url_matches.length;
						for (var u = 0; u < urls_number; u++) {
							var re = new RegExp(url_matches[u].replace(/([.?*+^$[\]\\(){}|-])/g, "\\$1"), "ig");
							final_text = final_text.replace(re, url_matches[u]);
						}
					}
				}
				return final_text;
			}

			// Abscond/reconnect button
			var abscond_button = $("#abscond_button").click(function() {
				if (status == "chatting") {
					if (confirm("Are you sure you want to abscond?")) { disconnect(); }
				} else if (chat.type == "searched") {
					location.href = "/search";
				} else {
					connect();
				}
			});


			// Global announcements
			var announcement_template = Handlebars.compile($("#announce_template").html());

			function announcement_banner(title, text, headercolor) {
				$("#global_announcements").append(announcement_template({
					announce: {
						title: title,
						text: text,
						headercolor: headercolor
					}
				}));
				setTimeout(function(){ $(".announcement").addClass("show"); }, 100);
			}

			body.on("click", ".announcement", function() {
				var announcement = $(this);
				announcement.removeClass("show");
				setTimeout(function() {
					announcement.remove();
				}, 1000)
			});

			// Theme specific code
			function update_theme(theme) {
				// empty placeholder here if we need js in future
			}

			// Run theme specific code.
			update_theme($("#theme_form select").val());

			// Now all that's done, let's connect
			connect();

		},
		"log": function(show_bbcode) {
			// Perform BBCode conversion
			$("#archive_conversation div p").each(function(line) { show_bbcode ? this.innerHTML = raw_bbencode(this.innerHTML, false) : $(this).html(bbremove(this.innerHTML)); });
		},
		"spamless": function(show_bbcode) {
			// Perform BBCode conversion
			$(".spam_table .message_content").each(function(line) { show_bbcode ? this.innerHTML = raw_bbencode(this.innerHTML, false) : $(this).html(bbremove(this.innerHTML)); });
		},
		// Broadcast page
		"broadcast": function() {
			$("input[name=title]").keyup(function() {
				$(".announcement h2").text(this.value);
			});

			$("textarea[name=text]").keyup(function() {
				$(".announcement p").text(this.value || "[no message]");
			});

			$("input[name=headercolor]").change(function() {
				$(".announcement").css("background-color", this.value);
			});
		},
	};
})();
