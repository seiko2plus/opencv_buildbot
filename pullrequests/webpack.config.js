var path = require('path');

const LoaderOptionsPlugin = require('webpack/lib/LoaderOptionsPlugin');
const LoaderDefinePlugin = require('webpack/lib/DefinePlugin');
const ExtractTextPlugin = require("extract-text-webpack-plugin");
const extractLess = new ExtractTextPlugin({
    filename: "styles.css",
});

pluginName = "pullrequests"
pluginPythonName = "opencv_pullrequests"

module.exports = {
    // devtool: "inline-source-map",

    entry: {
        scripts: "./src/module/main.module.coffee",
        styles: "./src/styles/styles.less",
        // tests: "./test/main.coffee",
    },
    output: {
        path: path.resolve(__dirname, "./"+pluginPythonName+"/static"),
        filename: "[name].js"
    },
    plugins: [
        extractLess,
        new LoaderOptionsPlugin({
            options: {
                ngClassify: {
                    appName: pluginName,
                    provider: {
                        suffix: 'Service'
                    }
                }
            }
        })
    ],

    resolve: {
        extensions: [".js", ".json"],
    },
    module: {
        rules: [
            {
                test: /\.coffee$/,
                use: ['coffee-loader', 'ng-classify-loader'],

            },
            // All files with a '.ts' or '.tsx' extension will be handled by 'ts-loader' or awesome-typescript-loader'.
            { test: /\.tsx?$/, loader: "awesome-typescript-loader" },

            // All output '.js' files will have any sourcemaps re-processed by 'source-map-loader'.
            {
                enforce: "pre",
                test: /\.js$/,
                loader: "source-map-loader",
            },
            {
                test: /\.css$/,
                loader: ExtractTextPlugin.extract("style-loader", "css-loader")
            },
            {
                test: /\.less$/,
                use: extractLess.extract({
                use: [{
                    loader: "css-loader"
                }, {
                    loader: "less-loader"
                }],
                // use style-loader in development
                fallback: "style-loader"
                })
            },
            { test: /\.jade$/, loader: 'pug-loader' },
            /*{
                test: /\.js$/,
                loader: "babel-loader",
                query: {
                    "presets": ["@babel/preset-env"]
                },
                exclude: "/node_modules/"
            },
            ,
            {
                loader: 'babel-loader',
                query: {
                    presets: ["@babel/preset-env"]
                },
                test: /\.js$/,
                exclude: /node_modules/
            }*/
        ],
    },
};