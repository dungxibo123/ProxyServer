# coding=utf-8
import os, sys, _thread, socket
import time
# Khai báo những object cần thiết
__BLACKLIST_PATH__ = "./blacklist.conf"
__RES_403_PATH__ = "./403/index.html"

# Hàm đọc file
def get403Respone(file):
    try:
        return ''.join(open(file,'r',encoding='utf8').readlines())

    except Exception as e:
        print(e)


def printout(type, request, address):
    print(address[0], "\t", type, "\t", request, "\t")


def getBlacklist(blackList):
    # Đọc file blacklist.conf
    f = open(blackList, "r")
    res = []
    for line in f:
        res.append(line.strip())

    f.close()
    return res


BLACKLIST_RESPONE = get403Respone(__RES_403_PATH__)
time.sleep(5)
print(BLACKLIST_RESPONE)
def proxy_thread(conn, client_addr):

    # Nhận request từ client - (max byte nhận được)
    try:
        request = conn.recv(
            999999
        )  # Sô byte tối đã khi nhận laf 9999999 #socket.socket.recv la nhan TCP
        print(request)
    except:
        pass

    # Chuyển request về dạng string để xử lý, vì request khi nhận được là bytes
    request = str(request, "utf-8")
    # Lấy dòng đầu tiên
    first_line = request.split("\n")[0]

    # Get url
    try:
        url = first_line.split(" ")[1]
        print("___URL___: ", url)
    except:
        url = ""

    # Đọc blacklist.conf vào BLOCKED
    BLOCK = getBlacklist(__BLACKLIST_PATH__)

    for i in range(0, len(BLOCK)):
        if (
            BLOCK[i] in url
        ):  # Nếu phát hiện url trong BLOCKED thì sẽ chặn lại và gửi lỗi 403 forbidden về cho user
            print("Blocked: ", url)
            conn.send(b"HTTP/1.1 403 Forbidden\n")
            conn.send(b"Content-Type: text/html\n")
            conn.send(b"\n\n")
            f = open(__RES_403_PATH__,'r',encoding='utf8')
            for line in f:
                conn.send(bytes(line.strip(),"utf-8"))
            conn.close()
            sys.exit(1)

    printout("Request", first_line, client_addr)

    # Tìm webserver và port             # Ví dụ: http://forum.vietstock.vn/
    http_pos = url.find("://")  # Tìm :// - (http)
    if http_pos == -1:  # Nếu không tìm thấy http
        temp = url  # Thì gán temp = url để tìm port
    else:
        temp = url[
            (http_pos + 3) :
        ]  # Nếu tìm thấy http thì temp = còn lại của url: - (www.kenh14.vn/)

    port_pos = temp.find(
        ":"
    )  # Tìm vị trí port (nếu có) - Ví dụ url: search.services.mozilla.com:443 => port là 443

    webserver_pos = temp.find("/")  # Tìm vị trí webserver của url : .vn/
    if webserver_pos == -1:
        webserver_pos = len(temp)  # Nếu ko thấy mặc định ở vị trí cuối

    webserver = ""  # Khởi tạo biến webserver
    port = -1  # Khởi tạo biến port
    if port_pos == -1 or webserver_pos < port_pos:  # Nếu không có port => port mặc định
        port = 80
        webserver = temp[:webserver_pos]
    else:  # Có port
        port = int((temp[(port_pos + 1) :])[: webserver_pos - port_pos - 1])
        webserver = temp[:port_pos]

    try:
        # Tạo socket để kết nối đến web server
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        skt.connect((webserver, port))
        skt.send(bytes(request, "utf-8"))  # Gửi request đến webserver

        while 1:
            # Nhận dữ liệu từ webserver
            data = skt.recv(999999)  # Sô byte tối đã khi nhận

            if data:
                # Gửi đến browser/client
                conn.send(data)
            else:
                break
        skt.close()
        conn.close()
    except Exception:  # Đóng kết nối nếu lỗi xảy ra
        if skt:
            skt.close()
        if conn:
            conn.close()
        printout("Reset", first_line, client_addr)
        sys.exit(1)


def main():
    # Host
    host = ""
    # Default port
    port = 8888

    print("Proxy server port: ", port, " - ", "Host: localhost")

    try:
        # Tạo socket - (socket_family ~ ipv4, socket_type ~ TCP, protocol (mặc định là 0))
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Liên kết hostname (ip) và port number vào socket.
        skt.bind((host, port))

        # Nghe TCP ... sẽ chứa được bao nhiêu connections # Đợi kết nối
        skt.listen(30)

    # Nếu không tạo được socket hoặc bị lỗi thì except
    except Exception as e:
        print(e)
        # Nếu đã tạo được socket

        if skt:
            # Đóng kết nối
            skt.close()
        print("Socket error! Connection closing!")  # Báo lỗi
        sys.exit(1)

    # Nếu đã nhận được kết nối tiếp tục đến khi báo lỗi hoặc user ngừng nó
    while 1:
        conn, client_addr = skt.accept()  # Khởi tạo kết nối TCP với client
        # Chặn và đợi cho kết nối kế tiếp
        # Return 1 socket object tượng trưng cho kết nối
        # và client address gồm (host, port)

        # Tạo 1 _thread để có thể nhận request
        _thread.start_new_thread(proxy_thread, (conn, client_addr))
	#tạo thread mới, gọi proxy_thread(conn,cli..))

    skt.close()


if __name__ == "__main__":
    main()
