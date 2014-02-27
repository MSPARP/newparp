function linkify(inputText) {
    var replacedText, replacePattern1, replacePattern2;

    //URLs starting with http://, https://, or ftp://
    replacePattern1 = /]?=?https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/gim;
    replacedText = inputText.replace(replacePattern1,
    function(m) {
        if (m.substr(0,1) == "=" || m.substr(0,1) == "]") {
            return m;
        } else {
            return "[url]"+m+"[/url]";
        }
    });

    //Change email addresses to mailto:: links.
    replacePattern2 = /(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})/gim;
    replacedText = replacedText.replace(replacePattern2, '[email]$1[/email]');

    return replacedText;
}

function cmobile() {
    if (navigator.userAgent.indexOf('Android')!=-1 || navigator.userAgent.indexOf('iPhone')!=-1 || navigator.userAgent.indexOf('Nintendo 3DS')!=-1 || navigator.userAgent.indexOf('Nintendo DSi')!=-1 || window.innerWidth<=500) {
        return true;
    } else {
        return false;
    }
}

var deviceDetection = function () {
    var osVersion,
    device,
    deviceType,
    userAgent,
    isSmartphoneOrTablet;
    
    device = (navigator.userAgent).match(/Android|iPhone|iPad|iPod/i); 
    
    if ( /Android/i.test(device) ) {
        if ( !/mobile/i.test(navigator.userAgent) ) {
            deviceType = 'tablet'; 
        } else {
            deviceType = 'phone';
        } 
    
        osVersion = (navigator.userAgent).match(/Android\s+([\d\.]+)/i);
        osVersion = osVersion[0];
        osVersion = osVersion.replace('Android ', ''); 
    
    } else if ( /iPhone/i.test(device) ) {
        deviceType = 'phone'; 
        osVersion = (navigator.userAgent).match(/OS\s+([\d\_]+)/i);
        osVersion = osVersion[0]; 
        osVersion = osVersion.replace(/_/g, '.'); 
        osVersion = osVersion.replace('OS ', '');
    
    } else if ( /iPad/i.test(device) ) { 
        deviceType = 'tablet'; 
        osVersion = (navigator.userAgent).match(/OS\s+([\d\_]+)/i); 
        osVersion = osVersion[0];
        osVersion = osVersion.replace(/_/g, '.');
        osVersion = osVersion.replace('OS ', '');
    } 
    isSmartphoneOrTablet = /Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent); 
    userAgent = navigator.userAgent; 
    
    return { 'isSmartphoneOrTablet': isSmartphoneOrTablet, 
             'device': device, 
             'osVersion': osVersion,
             'userAgent': userAgent,
             'deviceType': deviceType 
            };
}();

function glow(selector) {
    $(selector).css({
        'color' : '#C0F0C0',
    });
}

function unGlow(selector) {
    $(selector).css({
        'color' : ''
    });
}

$(document).ready(function() {
    var SEARCH_PERIOD = 1;
    var PING_PERIOD = 10;

    var SEARCH_URL = "/search";
    var SEARCH_QUIT_URL = "/stop_search";
    var POST_URL = "/chat_ajax/post";
    var SAVE_URL = "/chat_ajax/save";

    var CHAT_FLAGS = ['autosilence','public','nsfw'];

    var MOD_GROUPS = ['globalmod', 'mod', 'mod2', 'mod3']
    var GROUP_RANKS = { 'globalmod': 6, 'mod': 5, 'mod2': 4, 'mod3': 3, 'user': 2, 'silent': 1 }
    var GROUP_DESCRIPTIONS = {
        'globalmod': { title: 'Adoraglobal Mod', description: 'Charat Staff' },
        'mod': { title: 'Magical Mod', description: 'Silence, Kick and Ban' },
        'mod2': { title: 'Cute-Cute Mod', description: 'Silence and Kick' },
        'mod3': { title: 'Little Mod', description: 'Silence' },
        'user': { title: '', description: '' },
        'silent': { title: 'Silenced', description: '' },
    };

    var pingInterval;
    var chatState;
    var userState;
    var newState;
    var currentSidebar;
    var previewHidden = true;
    topicHidden = false;

    var actionListUser = null;
    var highlightUser = null;
    var blockUser = null;

    var ORIGINAL_TITLE = document.title;
    var CHAT_NAME = chat['title'] || chat['url'];
    var conversation = $('#conversation');
    
    var isActive;
    window.onfocus = function () {
      isActive = true;
    };
    window.onblur = function () {
      isActive = false;
    };

    function isCheckedById(id) {

        var checked = $("input[@id=" + id + "]:checked").length;

        if (checked == 0) {
            return false;
        } else {
            return true;
        }
    }

    var disnot = 1;
    var sysnot = 0;
    var topichide = 0;
    var oocset = 0;
    if (cmobile()) {
        var sidebarset = null;
    } else {
        var sidebarset = "userList";
    }
    var bbset = 1;
    var deskset = 0;

    //check variable
    if (disnot == 0) {
        $('.disnot').removeAttr('checked');
    } else {
        $('.disnot').attr('checked','checked');
    }

    if (sysnot == 1) {
        $('.sysnot').attr('checked','checked');
        $('.system').hide();
    }

    if (topichide == 1) {
        $('#topic').hide();
        topicHidden = true;
    }

    if (oocset == 1) {
        $('.oocset').attr('checked','checked');
        glow('#ooclet');
    } else {
        $('.oocset').removeAttr('checked');
    }

    if (bbset == 1) {
        $('.bbset').attr('checked','checked');
    } else {
        $('.bbset').removeAttr('checked');
    }

    if (deskset == 1) {
        $('.deskset').attr('checked','checked');
    } else {
        $('.deskset').removeAttr('checked');
    }

    //toggle
    $('.disnot').click(function() {
        if (this.checked) {
            disnot = 1;
        } else {
            disnot = 0;
        }
    });

    $('.sysnot').click(function() {
        if (this.checked) {
            sysnot = 1;
            $('.system').hide();
        } else {
            sysnot = 0;
            $('.system').show();
            conversation.scrollTop(conversation[0].scrollHeight);
        }
    });

    $('.oocset').click(function() {
        if (this.checked) {
            oocset = 1;
            glow('#ooclet');
        } else {
            oocset = 0;
            unGlow('#ooclet');
        }
        updateChatPreview();
    });

    $('#ooclet').click(function() {
        if (oocset == 0) {
            oocset = 1;
            $('.oocset').attr('checked','checked');
            glow('#ooclet');
        } else {
            oocset = 0;
            $('.oocset').removeAttr('checked');
            unGlow('#ooclet');
        }
        updateChatPreview();
    });
    
    $('#topbar .right span').click(function() {
        if ($(this).attr('class') == currentSidebar) {
            sidebarset = null;
            unGlow('.'+$(this).attr('class'));
            setSidebar(null);
        } else {
            sidebarset = $(this).attr('class');
            unGlow('#topbar .right span');
            glow('.'+$(this).attr('class'));
            setSidebar(sidebarset);
        }
    });

    $('.bbset').click(function() {
        if (this.checked) {
            bbset = 1;
        } else {
            bbset = 0;
        }
    });

    $('.deskset').click(function() {
        if (this.checked) {
            deskset = 1;
        } else {
            deskset = 0;
        }
    });

    $('#convo p').each(function() {
        if (bbset == 1) {
            line = bbEncode(linkify($(this).html()));
            $(this).html(line);
        } else {
            if ($(this).attr('class') == 'eMessages') {
                line = bbEncode(linkify($(this).html()));
            } else {
                line = bbEncode(linkify(bbRemove($(this).html())));
            }
            $(this).html(line);
        }
    });

    if ($('#topic').length != 0) {
        if (bbset == 1) {
            text = bbEncode(linkify($('#topic').html()));
            $('#topic').html(text);
        } else {
            text = bbEncode(linkify(bbRemove($('#topic').html())));;
            $('#topic').html(text);
        }
    }

    // Redirect iPhone/iPod visitors
    function isiPhone(){
        return (
            (navigator.platform.indexOf("iPhone") != -1) ||
            (navigator.platform.indexOf("iPod") != -1)
        );
    }

    $('input, select, button').attr('disabled', 'disabled');

    if (document.cookie=="") {

        $('<p>').css('color', '#FF0000').text('It seems you have cookies disabled. Unfortunately cookies are essential for MSPARP to work, so you\'ll need to either enable them or add an exception in order to use MSPARP.').appendTo(conversation);

        $('.controls').submit(function() {
            return false;
        });

    } else {

        // Search

        function runSearch() {
            $.post(SEARCH_URL, {}, function(data) {
                chat = data['target'];
                chaturl = '/chat/'+chat['url'];
                if (typeof window.history.replaceState!="undefined") {
                    window.history.replaceState('', '', chaturl);
                    startChat();
                } else {
                    window.location.replace(chaturl);
                }
            }).complete(function() {
                if (chatState=='search') {
                    window.setTimeout(runSearch, 1000);
                }
            });
        }

        // Chatting
        function addLine(msg){
            var von = conversation.scrollTop()+conversation.height()+24;
            var don = conversation[0].scrollHeight;
            var lon = don-von;
            if (lon <= 30){
                flip = 1;
            } else {
              $('#exclaim').html(parseInt($('#exclaim').html())+1);
            }

            if (bbset == 1) {
                message = bbEncode(htmlEncode(linkify(msg.text)));
            } else {
                message = bbEncode(htmlEncode(linkify(bbRemove(msg.text))));
            }

            msgClass = msg.type;
            var alias = "";
            if (msg.acronym) {
                alias = msg.acronym+": "
            }

            var mp = $('<p>').attr("id","message"+msg.id).addClass(msg.type).css('color', '#'+msg.color).html(alias+message).appendTo('#convo');

            /*
            if (highlightUser==msg.counter) {
                mp.addClass('highlight');
            }
            if (blockUser==msg.counter) {
                mp.addClass('blocking');
            }
            */

            if (sysnot == 1 && msgClass == 'system') {
                $('.system').hide();
            }

            if (flip == 1) {
                conversation.scrollTop(conversation[0].scrollHeight);
                flip = 0;
            }

            if (isActive == false && deskset == 1) {
                show(chat['url'],htmlEncode(bbRemove(msg.text)));
            }
            shownotif = 0;
        }

        function startChat() {
            chatState = 'chat';
            userState = 'online';
            document.title = (chat['title'] || chat['url'])+' - '+ORIGINAL_TITLE;
            if (chat.type=='unsaved' || chat.type=='saved') {
                document.title = ORIGINAL_TITLE+' - '+chat['url'];
            }
            msgcont = 0;
            conversation.removeClass('search');
            $('input, select, button').removeAttr('disabled');
            $('#preview').css('color', '#'+user.character.color);
            $('#logLink').attr('href', '/chat/'+chat['url']+'/log');
            if (!sidebarset) {
                setSidebar(null);
                unGlow('#topbar .right span');
            } else {
                setSidebar(sidebarset);
                unGlow('#topbar .right span');
                glow('#topbar .right .'+sidebarset);
            }
            //getMeta();
            getMessages();
            pingInterval = window.setTimeout(pingServer, PING_PERIOD*1000);
            updateChatPreview();
        }

        function getMeta() {
            var messageData = {'chat_id': chat['id'], 'after': '0'};
            $.post('/chat_api/messages', messageData, function(data) {
                messageParse(data,0);
            }, "json");
        }

        function getMessages() {
            var messageData = {'chat_id': chat['id'], 'after': latestNum};
            $.post('/chat_api/messages', messageData, function(data) {
                messageParse(data,1);
            }, "json").complete(function() {
                if (chatState=='chat') {
                    window.setTimeout(getMessages, 50);
                } else {
                    $('#save').appendTo(conversation);
                    $('#save input').removeAttr('disabled');
                    conversation.scrollTop(conversation[0].scrollHeight);
                }
            });
        }

        function messageParse(data,ape) {
            if (typeof data.exit!=='undefined') {
                if (data.exit=='kick') {
                    clearChat();
                    addLine({ counter: -1, color: '000000', text: 'You have been kicked from this chat. Please think long and hard about your behaviour before rejoining.' });
                } else if (data.exit=='ban') {
                    latestNum = -1;
                    chat = 'theoubliette'
                    $('#userList h1')[0].innerHTML = 'theoubliette';
                    $('#conversation').empty();
                }
                return true;
            }
            var messages = data.messages;
            for (var i=0; i<messages.length; i++) {
                if (ape == 1) {
                    addLine(messages[i]);
                    latestNum = Math.max(latestNum, messages[i]['id']);
                }
            }
            if (typeof data.counter!=="undefined") {
                user.meta.counter = data.counter;
            }
            if (typeof data.users!=="undefined") {
                // Reload user lists.
                actionListUser = null;
                $("#online > li, #idle > li").appendTo(holdingList);
                //generateUserlist(data.users, $('#online')[0]);
            }
            if (typeof data.meta!=='undefined') {
                // Reload chat metadata.
                var chat = data.meta;

                for (i=0; i<CHAT_FLAGS.length; i++) {
                    if (typeof data.meta[CHAT_FLAGS[i]]!=='undefined') {
                        $('#'+CHAT_FLAGS[i]).attr('checked', 'checked');
                        $('#'+CHAT_FLAGS[i]+'Result').show();
                    } else {
                        $('#'+CHAT_FLAGS[i]).removeAttr('checked');
                        $('#'+CHAT_FLAGS[i]+'Result').hide();
                    }
                }

                if (typeof data.meta.topic!=='undefined') {
                    $('#topic').html(bbEncode(linkify(data.meta.topic)));
                } else {
                    $('#topic').text('');
                }

                if (user.meta.group == 'mod' || user.meta.group == 'globalmod') {
                    $('.inPass').hide();
                    $('.editPass').show();
                } else {
                    $('.editPass').hide();
                    $('.inPass').show();
                }
                //NSFW
                if (data.meta['nsfw'] == '1') {
                    //Change
                } else {
                    //Changed
                }
            }
            if (messages.length>0 && typeof hidden!=="undefined" && document[hidden]==true && ape == 1) {
                if (msgClass == "system" && sysnot == 1) {}
                else {
                    msgcont++;
                    msss = "Messages";
                    if (msgcont == 1) {
                        msss = "Message";
                    }
                    document.title = msgcont+" New "+msss+" - "+chat['url'];
                }
            }
            if (user.meta.group == 'mod' || user.meta.group == 'globalmod') {
                $('.inPass').hide();
                $('.editPass').show();
                $('.opmod input').removeAttr('disabled');
            } else {
                $('.editPass').hide();
                $('.inPass').show();
                $('.opmod input').attr('disabled', 'disabled');
            }
        }

        function pingServer() {
            $.post('/chat_api/ping', {'chat_id': chat['id']});
            pingInterval = window.setTimeout(pingServer, PING_PERIOD*1000);
            updateChatPreview();
        }

        function disconnect() {
            if (confirm('Are you sure you want to disconnect?')) {
                $.ajax('/chat_api/quit', {'type': 'POST', data: {'chat_id': chat['id']}});
                clearChat();
            }
        }

        function clearChat() {
            chatState = 'inactive';
            if (pingInterval) {
                window.clearTimeout(pingInterval);
            }
            $('input[name="chat"]').val(chat['url']);
            $('input, select, button').attr('disabled', 'disabled');
            $('#userList > ul').empty();
            setSidebar(null);
            document.title = (chat['title'] || chat['url'])+' - '+ORIGINAL_TITLE;
            if (chat.type=='unsaved' || chat.type=='saved') {
                document.title = ORIGINAL_TITLE+' - '+chat['url'];
            }
            msgcont = 0;
        }

        // Sidebars

        function setSidebar(sidebar) {
            if (currentSidebar) {
                $('#'+currentSidebar).hide();
            } else {
                $(document.body).addClass('withSidebar');
            }
            // Null to remove sidebar.
            if (sidebar) {
                $('#'+sidebar).show();
            } else {
                $(document.body).removeClass('withSidebar');
            }
            currentSidebar = sidebar;
            var crom = conversation.scrollTop()+conversation.height()+24;
            var den = conversation[0].scrollHeight;
            var lon = den-crom;
            if (lon <= 50){
                conversation.scrollTop(conversation[0].scrollHeight);
            }
        }

        function closeSettings() {
            //findit
            if ($(document.body).hasClass('mobile')) {
                if (navigator.userAgent.indexOf('Nintendo 3DS')!=-1 || navigator.userAgent.indexOf('Nintendo DSi')!=-1) {} {
                    setSidebar(null);
                }
                unGlow('#topbar .right span');
            } else {
                unGlow('#topbar .right span');
                glow('#topbar .right .userList');
                setSidebar('userList');
            }
        }

        // User list
        var holdingList = $("<ul />");
        /*
        function generateUserlist(users, listElement) {
            for (var i=0; i<users.length; i++) {
                var currentUser = users[i];
                // Get or create a list item.
                var listItem = $(holdingList).find('#user'+currentUser.meta.counter);
                if (listItem.length==0) {
                    var listItem = $('<li />').attr('id', 'user'+currentUser.meta.counter);
                    listItem.click(showActionList);
                }
                // Name is a reserved word; this may or may not break stuff but whatever.
                var userStatus = "";
                if (currentUser.character['status']) {
                    userStatus = currentUser.character['status']+'!';
                }
                listItem.css('color', '#'+currentUser.character.color).text(userStatus+currentUser.character['name']+" ["+currentUser.character['acronym']+"]");
                listItem.removeClass().addClass(currentUser.meta.group);
                var currentGroup = GROUP_DESCRIPTIONS[currentUser.meta.group]
                var userTitle = currentGroup.title
                if (currentGroup.description!='') {
                    userTitle += ' - '+GROUP_DESCRIPTIONS[currentUser.meta.group].description
                }
                listItem.attr('title', userTitle);
                if (currentUser.meta.counter==user.meta.counter) {
                    // Set self-related things here.
                    if (currentUser.meta.group=='silent') {
                        // Just been made silent.
                        $('#textInput, .controls button[type="submit"]').attr('disabled', 'disabled');
                    } else if (user.meta.group=='silent' && currentUser.meta.group!='silent') {
                        // No longer silent.
                        $('input, select, button').removeAttr('disabled');
                    }
                    user.meta.group = currentUser.meta.group;
                    if ($.inArray(user.meta.group, MOD_GROUPS)==-1) {
                        $(document.body).removeClass('modPowers');
                    } else {
                        $(document.body).addClass('modPowers');
                    }
                    listItem.addClass('self').append(' (you)');
                    $('#textInput').css('color','#'+currentUser.character.color);
                }
                listItem.append("<span class=\"userID\">user"+currentUser.meta.counter+"</span>");
                listItem.removeData().data(currentUser).appendTo(listElement);
            }
        }
        */

        function showActionList() {
            $('#actionList').remove();
            // Hide if already shown.
            if (this!=actionListUser) {
                var actionList = $('<ul />').attr('id', 'actionList');
                var userData = $(this).data();
                if (userData.meta.counter==highlightUser) {
                    $('<li />').text('Clear highlight').appendTo(actionList).click(function() { highlightPosts(null); });
                } else {
                    $('<li />').text('Highlight posts').appendTo(actionList).click(function() { highlightPosts(userData.meta.counter); });
                               }

                if (userData.meta.counter==blockUser) {
                    $('<li />').text('Unblock').appendTo(actionList).click(function() { blockPosts(null); });
                } else {
                    $('<li />').text('Block').appendTo(actionList).click(function() { blockPosts(userData.meta.counter); });
                }

                // Mod actions. You can only do these if you're (a) a mod, and (b) higher than the person you're doing it to.
                if ($.inArray(user.meta.group, MOD_GROUPS)!=-1 && GROUP_RANKS[user.meta.group]>=GROUP_RANKS[userData.meta.group]) {
                    for (var i=1; i<MOD_GROUPS.length; i++) {
                        if (userData.meta.group!=MOD_GROUPS[i] && GROUP_RANKS[user.meta.group]>=GROUP_RANKS[MOD_GROUPS[i]]) {
                            var command = $('<li />').text('Make '+GROUP_DESCRIPTIONS[MOD_GROUPS[i]].title);
                            command.appendTo(actionList);
                            command.data({ group: MOD_GROUPS[i] });
                            command.click(setUserGroup);
                        }
                    }
                    if ($.inArray(userData.meta.group, MOD_GROUPS)!=-1) {
                        $('<li />').text('Unmod').appendTo(actionList).data({ group: 'user' }).click(setUserGroup);
                    }
                    if (userData.meta.group=='silent') {
                        $('<li />').text('Unsilence').appendTo(actionList).data({ group: 'user' }).click(setUserGroup);
                    } else {
                        $('<li />').text('Silence').appendTo(actionList).data({ group: 'silent' }).click(setUserGroup);
                    }
                    $('<li />').text('Kick').appendTo(actionList).data({ action: 'kick' }).click(userAction);
                    $('<li />').text('IP Ban').appendTo(actionList).data({ action: 'ip_ban' }).click(userAction);
                }
                $(actionList).appendTo(this);
                actionListUser = this;
            } else if (this==actionListUser) {
                actionListUser = null;
            }
        }

        function setUserGroup() {
            var counter = $(this).parent().parent().data().meta.counter;
            var group = $(this).data().group;
            if (counter!=user.meta.counter || confirm('You are about to unmod yourself. Are you sure you want to do this?')) {
                $.post(POST_URL,{'chat_id': chat['id'], 'set_group': group, 'counter': counter});
            }
        }

        function userAction() {
            var counter = $(this).parent().parent().data().meta.counter;
            var action = $(this).data().action;
            var actionData = {'chat_id': chat['id'], 'user_action': action, 'counter': counter};
            if (action=='ip_ban') {
                var reason = prompt('Please enter a reason for this ban (spamming, not following rules, etc.):');
                if (reason==null) {
                    return;
                } else if (reason!="") {
                    actionData['reason'] = reason;
                }
            }
            if (counter!=user.meta.counter || confirm('You are about to kick and/or ban yourself. Are you sure you want to do this?')) {
                $.post(POST_URL, actionData);
            }
        }

        function highlightPosts(counter) {
            $('.highlight').removeClass('highlight');
            if (counter!=null) {
                $('.user'+counter).addClass('highlight');
            }
            highlightUser = counter;
        }

        function blockPosts(counter) {
            $('.blocking').removeClass('blocking');
            if (counter!=null) {
                $('.user'+counter).addClass('blocking');
            }
            conversation.scrollTop(conversation[0].scrollHeight);
            blockUser = counter;
        }

        /* Browser compatibility for visibilityChange */
        var hidden, visibilityChange;
        if (typeof document.hidden !== "undefined") {
            hidden = "hidden";
            visibilityChange = "visibilitychange";
        } else if (typeof document.mozHidden !== "undefined") {
            hidden = "mozHidden";
            visibilityChange = "mozvisibilitychange";
        } else if (typeof document.msHidden !== "undefined") {
            hidden = "msHidden";
            visibilityChange = "msvisibilitychange";
        } else if (typeof document.webkitHidden !== "undefined") {
            hidden = "webkitHidden";
            visibilityChange = "webkitvisibilitychange";
        }

        // Event listeners
        function readCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        $('.controls').submit(function() {
            $('#textInput').focus();
            if (updateChatPreview()) {
                if (jQuery.trim($('#textInput').val())=='/ooc') {
                    oocset = 1;
                    glow('#ooclet');
                    $('.oocset').attr('checked','checked');
                    $('#textInput').val('');
                    return false;
                } else if (jQuery.trim($('#textInput').val())=='/ic') {
                    oocset = 0;
                    unGlow('#ooclet');
                    $('.oocset').removeAttr('checked');
                    $('#textInput').val('');
                    return false;
                }

                if (!$('#textInput').val()) {
                    return false;
                }

                if (jQuery.trim($('#textInput').val())=='/usr') {
                    alert(readCookie('session'));
                    $('#textInput').val('');
                } else if ($('#textInput').val()!='') {
                    if (pingInterval) {
                        window.clearTimeout(pingInterval);
                    }
                    var lineSend = $('#preview').text();
                    $.post('/chat_api/send',{'chat_id': chat['id'], 'text': lineSend}); // todo: check for for error
                    pingInterval = window.setTimeout(pingServer, PING_PERIOD*1000);
                    $('#textInput').val('');
                    updateChatPreview();
                } else if (textPreview.substr(0,4)=='/usr') {
                    textPreview = textPreview.substr(4);
                    alert(readCookie('session'));
                    $('#textInput').val('');
                }
            }
            if (cmobile()) {} else {
                $("#textInput").focus();
            }
            $('#textInput').val('');
            return false;
        });

        $("textarea#textInput").on('keydown', function(e) {
            if (!cmobile()) {
                if (e.keyCode == 13 && !e.shiftKey)
                {
                    e.preventDefault();
                    $('.controls').submit();
                }
            }
        });
        
        $("#statusInput").on('keydown', function(e) {
            if (e.keyCode == 13) {
                $('#statusButton').click();
            }
        });

        function updateChatPreview(){
            var textPreview = $('#textInput').val().replace(/\r\n|\r|\n/g,"[br]");
            textPreview = jQuery.trim(textPreview);

            if ($('#textInput').val().substr(0,1)=='/' && textPreview.substr(0,4)!=='/ooc' && textPreview.substr(0,3)!=='/ic' && textPreview.substr(0,3)!=='/me') {
                textPreview = textPreview.substr(1);
            }

            if (textPreview.substr(0,4)=='/ooc') {
                textPreview = jQuery.trim(textPreview.substr(4));
                if (textPreview.substr(0,3)=='/me') {
                    textPreview = "(( -"+jQuery.trim(textPreview.substr(3))+"- ))";
                } else {
                    textPreview = "(( "+textPreview+" ))";
                }
            } else if (textPreview.substr(0,3)=='/ic') {
                textPreview = textPreview.substr(3);
                if (textPreview.substr(0,3)=='/me') {
                    textPreview = "-"+jQuery.trim(textPreview.substr(3))+"-";
                }
            } else if (oocset == 1) {
                if (textPreview.substr(0,3)=='/me') {
                    textPreview = "(( -"+jQuery.trim(textPreview.substr(3))+"- ))";
                } else {
                    textPreview = "(( "+textPreview+" ))";
                }
            } else if (oocset == 0) {
                if (textPreview.substr(0,3)=='/me') {
                    textPreview = "-"+jQuery.trim(textPreview.substr(3))+"-";
                }
            }

            textPreview = jQuery.trim(textPreview);

            if ($('#textInput').val().substr(0,1)!=='/') {
                textPreview = applyQuirks(textPreview);
            }

            if (jQuery.trim($('#textInput').val())=='/ic') {
                textPreview = 0;
            }

            if (textPreview.length>0) {
                textPreview = textPreview.replace(/\s+/g, ' ');
                $('#preview').text(textPreview);
            } else {
                $('#preview').html('&nbsp;');
            }
            $('#conversation').css('bottom',($('.controls').height()+20)+'px');
            return textPreview.length!=0;
            // Hide if typing at bottom
        }

        $('#textInput').change(updateChatPreview).keyup(updateChatPreview).change();

        $("#textInput").on('keydown', function() {
            var num = 1489;
            if ($('#preview').html().length > num) {
                values = $(this).val();
                values = values.substr(0,num+3);
                $(this).val(values);
            }
        });

        $('#hidePreview').click(function() {
            if (previewHidden) {
                 $(this).text("Hide Preview");
            } else {
                $(this).text("Show Preview");
            }
            pretog();
        });

        function pretog() {
            if (previewHidden) {
                 $('#preview').show();
            } else {
                $('#preview').hide();
            }
            updateChatPreview();
            previewHidden = !previewHidden;
            return false;
        }

        if (typeof document.addEventListener!=="undefined" && typeof hidden!=="undefined") {
            document.addEventListener(visibilityChange, function() {
                if (chatState=='chat' && document[hidden]==false) {
                    if (navigator.userAgent.indexOf('Chrome')!=-1) {
                        // You can't change document.title here in Chrome. #googlehatesyou
                        window.setTimeout(function() {
                            document.title = (chat['title'] || chat['url'])+' - '+ORIGINAL_TITLE;
                            if (chat.type=='unsaved' || chat.type=='saved') {
                                document.title = ORIGINAL_TITLE+' - '+chat['url'];
                            }
                            msgcont = 0;
                        }, 200);
                    } else {
                        document.title = chat['url']+' - '+ORIGINAL_TITLE;
                        if (chat.type=='unsaved' || chat.type=='saved') {
                            document.title = ORIGINAL_TITLE+' - '+chat['url'];
                        }
                        msgcont = 0;
                    }
                }
            }, false);
        }

        $('#disconnectButton').click(disconnect);

        $('#statusButton').click(function() {
            newState = $('#statusInput').val();
            $('#statusInput').val('');
            $.post(POST_URL, {'chat_id': chat['id'], 'state': newState}, function(data) {
                userState = newState;
            });
        });

        $('#settingsButton').click(function() {
            setSidebar('settings');
        });

        $('.add').click(function() {
            $('#settings').submit();
        });

        $('#settings').submit(function() {
            // Trim everything first
            formInputs = $('#settings').find('input, select');
            for (i=0; i<formInputs.length; i++) {
                formInputs[i].value = jQuery.trim(formInputs[i].value)
            }
            if ($('input[name="name"]').val()=="") {
                alert("You can't chat with a blank name!");
            } else if ($('input[name="color"]').val().match(/^[0-9a-fA-F]{6}$/)==null) {
                alert("You entered an invalid hex code. Try using the color picker.");
            } else {
                var formData = $(this).serializeArray();
                formData.push({ name: 'chat_id', value: chat['id'] })
                $.post(SAVE_URL, formData, function(data) {
                    $('#preview').css('color', '#'+$('input[name="color"]').val());
                    var formInputs = $('#settings').find('input, select');
                    for (i=0; i<formInputs.length; i++) {
                        if (formInputs[i].name!="quirk_from" && formInputs[i].name!="quirk_to") {
                            user.character[formInputs[i].name] = formInputs[i].value;
                        }
                    }
                    user.character.replacements = [];
                    var replacementsFrom = $('#settings').find('input[name="quirk_from"]');
                    var replacementsTo = $('#settings').find('input[name="quirk_to"]');
                    for (i=0; i<replacementsFrom.length; i++) {
                        if (replacementsFrom[i].value!="" && replacementsFrom[i].value!=replacementsTo[i].value) {
                            user.character.replacements.push([replacementsFrom[i].value, replacementsTo[i].value])
                        }
                    }
                    closeSettings();
                });
            }
            return false;
        });

		//	
		// CONTINUE HERE
		//
        $('#metaOptions input').click(function() {
            var data = {'chat_id': chat['id'], 'meta_change': ''}
            // Convert to integer then string.
            data[this.id] = +this.checked+'';
            $.post(POST_URL, data);
        });

        $('#topicButton').click(function() {
            if ($.inArray(user.meta.group, MOD_GROUPS)!=-1) {
                var new_topic = prompt('Please enter a new topic for the chat:');
                if (new_topic!=null) {
                    $.post(POST_URL,{'chat_id': chat['id'], 'topic': new_topic.substr(0, 1400)});
                }
            }
        });
        
        $('.inPass').click(function() {
            var admin_pass = prompt('Enter your Admin Password:');
            if (admin_pass!=null) {
                $.post(POST_URL,{'chat_id': chat['id'], 'modPass': admin_pass.substr(0, 150), 'counter': user.meta.counter});
            }
        });

        $('.editPass').click(function() {
            if (user.meta.group == 'globalmod') {
                var admin_pass = prompt('Enter the new Admin Password:');
                if (admin_pass!=null) {
                    $.post(POST_URL,{'chat_id': chat['id'], 'editPass': admin_pass.substr(0, 150), 'counter': user.meta.counter});
                }
            } else if (user.meta.group == 'mod') {
                var admin_old_pass = prompt('Enter the old Admin Password:');
                var admin_pass = prompt('Enter the new Admin Password:');
                if (admin_pass!=null) {
                    if (admin_old_pass!=null){} else {
                        admin_old_pass == '';
                    }
                    $.post(POST_URL,{'chat_id': chat['id'], 'oldPass': admin_old_pass.substr(0, 150), 'editPass': admin_pass.substr(0, 150), 'counter': user.meta.counter});
                }
            }
        });

        $('.hidedesc').click(function() {
            if (topicHidden) {
                topichide = 0;
                $('#topic').show();
            } else {
                topichide = 1;
                $('#topic').hide();
            }
            topicHidden = !topicHidden;
            return false;
        });

        // Activate mobile mode on small screens
        if (cmobile()) {
            unGlow('#topbar .right span');
            setSidebar(null);
            $('.sidebar .close').click(function() {
                setSidebar(null);
            }).show();
            $('#userListButton').click(function() {
                setSidebar('userList');
            }).show();
        }

        window.onbeforeunload = function (e) {
            if (disnot == 1) {
                if (chatState=='chat') {
                    if (typeof e!="undefined") {
                        e.preventDefault();
                    }
                    return 'Are you sure you want to leave? Your chat is still running.';
                }
            }
        }

        $(window).unload(function() {
            if (chatState=='chat') {
                $.ajax('/chat_api/quit', {'type': 'POST', data: {'chat_id': chat['id']}, 'async': false});
            } else if (chatState=='search') {
                $.ajax(SEARCH_QUIT_URL, {'type': 'POST', 'async': false});
            }
        });

        // Initialisation

        if (chat==null) {
            chatState = 'search';
            document.title = 'Searching - '+ORIGINAL_TITLE;
            conversation.addClass('search');
            runSearch();
        } else {
            startChat();
        }

    }
    $('#conversation').scrollTop($('#conversation')[0].scrollHeight);
    if (!cmobile()) {
        $("#textInput").focus();
    }
    var crom = conversation.scrollTop()+conversation.height()+24;
    var den = conversation[0].scrollHeight;
    $(window).resize(function(e) {
        var lon = den-crom;
        if (lon <= 50){
            conversation.scrollTop(conversation[0].scrollHeight);
        }
    });

    if (deviceDetection.device == "iPhone" || deviceDetection.device == "iPad") {
        if (deviceDetection.osVersion.substr(0,3) < 5.1) {//gohere
            $('#conversation').kinetic();
        }
    }

    $("#textInput").click(function() {
        setTimeout(function(){
            var von = conversation.scrollTop()+conversation.height()+24;
            var don = conversation[0].scrollHeight;
            var lon = don-von;
            if (lon <= 30){
                conversation.scrollTop(conversation[0].scrollHeight);
            }
            $("#textInput").focus();
        }, 1);
    });

    // Exclaim the Keikaku
    $('#conversation').scroll(function(){
        var von = conversation.scrollTop()+conversation.height()+24;
        var don = conversation[0].scrollHeight;
        var lon = don-von;
        if (lon <= 30){
            $('#exclaim').html(0);
        }
    });

    $('#extain').click(function(){
        $('#exclaim').html(0);
        conversation.scrollTop(conversation[0].scrollHeight);
    });

    $('#saveLink').click(function() {
        if (confirm('Are you sure you want to save the log and disconnect?')) {
            $.ajax('/chat_api/quit', {'type': 'POST', data: {'chat_id': chat['id']}});
            clearChat();
            $('#save input').removeAttr('disabled');
            $('#saveLinking').click();
        }
    });

    $('#conversation p .spoiler').on('click', function() {
        if ($(this).css('opacity') == '0') {
            $(this).css('opacity','1');
        } else {
            $(this).css('opacity','0');
        }
    });

});
