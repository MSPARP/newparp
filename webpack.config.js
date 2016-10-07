var path = require("path"),
	webpack = require("webpack"),
	ExtractTextPlugin = require("extract-text-webpack-plugin");

var root = "./frontend"

module.exports = {
	entry: {
		vendor: ["jquery", "handlebars", "jstimezonedetect", "raven-js", "spectrum-colorpicker"],
		newparp: root + "/newparp.js",
	},
	devtool: "source-map",
	output: {
		path: "./newparp/static/assets",
		publicPath: "/static/assets/",
		filename: "[name].js"
	},
	resolve: {
		extensions: ["", ".js", ".scss"],
		alias: {
			handlebars: "handlebars/dist/handlebars.min.js",
		}
	},
	module: {
		loaders: [
			{
				test: /\.js$/i,
				exclude: /node_modules/,
				loader: "babel?presets[]=es2015"
			},
			{
				test: /\.scss$/i,
				loader: ExtractTextPlugin.extract("css!sass")
			},
			{
				test: /\.css$/i,
				loader: ExtractTextPlugin.extract("css")
			}
		]
	},
	plugins: [
		new ExtractTextPlugin("[name].css"),
		new webpack.DefinePlugin({
			"process.env": {
				NODE_ENV: '"production"'
			}
		}),
		new webpack.optimize.CommonsChunkPlugin({
			name: "vendor"
		}),
		new webpack.NoErrorsPlugin()
	]
}