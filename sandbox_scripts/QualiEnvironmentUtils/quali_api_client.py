import json

__author__ = 'eric.r'

SERVER_VERSION = '7.1.0'

import re
from zipfile import ZipFile
from io import BytesIO
import urllib2

def urlencode(s):
    return s.replace('+', '%2B').replace('/', '%2F').replace('=', '%3D')

class QualiAPIClient(object):
    def __init__(self, ip, port, username, password, domain):
        self.ip = ip
        self.port = port
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request('http://'+ip+':'+str(port)+'/API/Auth/Login',
                                  data='username='+username+'&password='+urlencode(password)+'&domain='+domain)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        backup = request.get_method
        request.get_method = lambda: 'PUT'
        url = opener.open(request)
        self.token = url.read()
        self.token = re.sub(r'^"', '', self.token)
        self.token = re.sub(r'"$', '', self.token)
        request.get_method = backup
    
    def download_environment_zip(self, toponames, zipfilename):
        if not isinstance(toponames, list):
            toponames = [toponames]
        fd = '{ "TopologyNames": ["'+("','".join(toponames))+'"] }'
        request = urllib2.Request('http://'+self.ip+':'+str(self.port)+'/API/Package/ExportPackage', data=fd)
        backup = request.get_method
        request.get_method = lambda: 'POST'
        request.add_header('Authorization', 'Basic '+self.token)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Accept', '*/*')
        request.add_header('Content-Length', str(len(fd)))
        request.get_method = backup
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        url = opener.open(request)
        
        zipcontent = url.read()
        with open(zipfilename, 'wb') as f:
            f.write(zipcontent)
        
    
    def upload_environment_zip_file(self, zipfilename):
        with open(zipfilename, 'rb') as g:
            zipdata = g.read()
            self._upload_environment_zip_data(zipdata)
    
    def _upload_environment_zip_data(self, zipdata):
        zipdata2 = zipdata
        
        boundary = b'''------------------------652c70c071862fc2'''
        
        fd = b'''--''' + boundary + \
             b'''\r\nContent-Disposition: form-data; name="file"; filename="my_zip.zip"\r\nContent-Type: application/octet-stream\r\n\r\n''' + \
             zipdata2 + \
             b'''\r\n--''' + boundary + b'''--\r\n'''
        
        class FakeReader(object):
            def __init__(self, k):
                self.k = k
                self.offset = 0
            
            def read(self, blocksize):
                if self.offset >= len(self.k):
                    return None
                
                if self.offset + blocksize >= len(self.k):
                    rv = self.k[self.offset:]
                    self.offset = len(self.k)
                else:
                    rv = self.k[self.offset:self.offset+blocksize]
                    self.offset += blocksize
                # print 'read '+rv
                return rv
        
        fdreader = FakeReader(fd)
        
        request = urllib2.Request('http://'+self.ip+':'+str(self.port)+'/API/Package/ImportPackage', data=fdreader)
        backup = request.get_method
        request.get_method = lambda: 'POST'
        # request.add_header('User-Agent', 'curl/7.39.0')
        request.add_header('Authorization', 'Basic '+self.token)
        # request.add_header('Host', '192.168.41.80:9000')
        # request.add_header('Content-Disposition', 'form-data; name="QualiPackage"; filename="package.zip"')
        # request.add_header('Content-Type', 'application/x-zip-compressed')
        request.add_header('Content-Type', 'multipart/form-data; boundary='+boundary)
        # request.add_header('Expect', '100-continue')
        request.add_header('Accept', '*/*')
        request.add_header('Content-Length', str(len(fd)))
        # request.add_header('Content-Type', 'application/zip')
        request.get_method = backup
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        url = opener.open(request)
        
        try:
            s = url.read()
            o = json.loads(s)
            if 'Success' not in o:
                raise Exception('"Success" value not found in Quali API response: ' + str(o))
        except Exception as ue:
            raise Exception('Error extracting Quali API zip import result: ' + str(ue))
        
        if not o['Success']:
            raise Exception('Error uploading Quali API zip package: '+o['ErrorMessage'])

