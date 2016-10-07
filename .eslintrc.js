module.exports = {
    "env": {
        "browser": true,
        "commonjs": true,
        "es6": true
    },
    "extends": "eslint:recommended",
    "parserOptions": {
        "sourceType": "module"
    },
    "rules": {
        "indent": [
            "error",
            "tab",
            {"SwitchCase": 1}
        ],
        "linebreak-style": [
            "error",
            "unix"
        ],
        "quotes": [
            "error",
            "double",
            {"allowTemplateLiterals": true, "avoidEscape": true}
        ],
        "semi": [
            "error",
            "always"
        ],
        "no-constant-condition": [
            "error",
            {"checkLoops": false}
        ],
        "no-empty": [
            "error",
            {"allowEmptyCatch": true}
        ],
        "no-unused-vars": [
            "warn"
        ],
        "no-console": [
            "off"
        ]
    }
};