function applyQuirks(text,pattern) {

    // Case
    switch (pattern['case']) {
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
            var buffer = text.replace(/[a-zA-Z]/g, function(t) {
                var out = t.toUpperCase();
                if (out==t) {
                    return t.toLowerCase();
                } else {
                    return out;
                }
            }).replace(/\bI\b/g, 'i').replace(/,\s*[A-Z]/g, function(t) { return t.toLowerCase(); });
            text = buffer.charAt(0).toLowerCase()+buffer.substr(1);
            break;
        case "alternating":
            var buffer = text.toLowerCase().split('');
            for(var i=0; i<buffer.length; i+=2){
                buffer[i] = buffer[i].toUpperCase();
            }
            text = buffer.join('');
            break;
    }

    // Replacements
    var replace = {};
    for (i=0; i<pattern.replacements.length; i++) {
        var replacement = pattern.replacements[i];
        replace[replacement[0]] = replacement[1];
    }
    
    var regex = {};
    for (i=0; i<pattern.regexes.length; i++) {
        var re = pattern.regexes[i];
        regex[re[0]] = re[1];
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
    
    if (!empty) {
        var replacementStrings = Object.keys(replace);
        for (i=0;i<replacementStrings.length;i++) {
            replacementStrings[i] = replacementStrings[i].replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
        }
        var regexStrings = Object.keys(regex);
        console.log(regexStrings);
        console.log(replacementStrings.join("|")+"|"+regexStrings.join("|"));
        var reg_from = new RegExp(replacementStrings.join("|")+"|"+regexStrings.join("|"), "g");
        text = text.replace(reg_from, function($1) {
            return replace[$1] ? replace[$1] : regex[$1];
        });
    }

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