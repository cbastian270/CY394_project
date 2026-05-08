FROM httpd:2.4-alpine

RUN sed -i 's/#LoadModule proxy_module/LoadModule proxy_module/' /usr/local/apache2/conf/httpd.conf && sed -i 's/#LoadModule proxy_http_module/LoadModule proxy_http_module/' /usr/local/apache2/conf/httpd.conf && echo 'Include conf/extra/cadetcoin.conf' >> /usr/local/apache2/conf/httpd.conf

COPY cadetcoin.conf /usr/local/apache2/conf/extra/cadetcoin.conf