mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
[theme]\n\
base=\"dark\"\n\
font=\"monospace\"\n\
" > ~/.streamlit/config.toml