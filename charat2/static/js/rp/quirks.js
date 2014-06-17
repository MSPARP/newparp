function applyQuirks(text,pattern) {

    // Case
    try {
        switch (pattern.case) {
            case "lower":
                text = text.toLowerCase();
                break;
            case "upper":
                text = text.toUpperCase();
                break;
            case "title":
                text = text.toLowerCase().replace(/\b\w/g, function(t) { return t.toUpperCase(); });
                break;
            case "inverted":
                var text = text.replace(/[a-zA-Z]/g, function(t) {
                    var out = t.toUpperCase();
                    if (out==t) {
                        return t.toLowerCase();
                    } else {
                        return out;
                    }
                });
                break;
            case "alternating":
                var buffer = text.toLowerCase().split('');
                for(var i=0; i<buffer.length; i+=2){
                    buffer[i] = buffer[i].toUpperCase();
                }
                text = buffer.join('');
                break;
            case "alt-lines":
                console.log('a');
                var buffer = text.toLowerCase().split(' ');
                for(var i=0; i<buffer.length; i+=2){
                    buffer[i] = buffer[i].toUpperCase();
                    console.log(test);
                }
                text = buffer.join(' ');
                console.log(text);
                break;
        }
    } catch(e) {}

    // Replacements
    try {
        var replace = {};
        for (i=0; i<pattern.replacements.length; i++) {
            var replacement = pattern.replacements[i];
            replace[replacement[0]] = replacement[1];
        }
    } catch(e) {
        replace = {};
    }
    
    try {
        var regex = {};
        for (i=0; i<pattern.regexes.length; i++) {
            var re = pattern.regexes[i];
            regex[re[0]] = re[1];
        }
    } catch(e) {
        regex = {};
    }

    var empty = true;
    for(var key in replace) {
        empty = false;
        break;
    }
    for(var key in regex) {
        empty = false;
        break;
    }
    
    try {
        if (!empty) {
            try {
                var replacementStrings = Object.keys(replace);
            } catch(e) {
                var replacementStrings = [];
            }
            for (i=0;i<replacementStrings.length;i++) {
                replacementStrings[i] = replacementStrings[i].replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
            }
            try {
                var regexStrings = Object.keys(regex);
            } catch(e) {
                var regexStrings = [];
            }
            if (replacementStrings.length!=0 && regexStrings.length!=0) {
                var reg_from = new RegExp(replacementStrings.join("|")+"|"+regexStrings.join("|"), "g");
            } else if (replacementStrings.length!=0 && regexStrings.length==0) {
                var reg_from = new RegExp(replacementStrings.join("|"), "g");
            } else if (replacementStrings.length==0 && regexStrings.length!=0) {
                var reg_from = new RegExp(regexStrings.join("|"), "g");
            } else {
                var reg_from = new RegExp("", "g");
            }
            text = text.replace(reg_from, function($1) {
                if (replace[$1]) {
                    return replace[$1]
                } else {
                    for (var reg in regexStrings) {
                        var original_text = $1;
                        if (RegExp(regexStrings[reg],'g').test($1)) {
                            var insert_text = regex[regexStrings[reg]];
                            insert_text = insert_text.replace(/([^\\]|^)(\$1)/g, function($1,$2,$3) {
                                return $2+original_text;
                            });
                            insert_text = insert_text.replace(/\\\$1/g, "\$1");
                            return insert_text;
                        }
                    }
                }
                return "";
            });
        }
    } catch(e) {}

    // Prefix
    if (pattern.quirk_prefix) {
        text = pattern.quirk_prefix+' '+text;
    }
    
    // Suffix
    if (pattern.quirk_suffix) {
        text = text+' '+pattern.quirk_suffix;
    }

    return text
}

function depunct(txt) {
    return txt.replace(/[.,?!']/g, '');
}