# Backend Hosting Options

Tai lieu nay tong hop cac huong thay the de chay backend cho giao dien QC web, thay vi dung `127.0.0.1:8000` tren GitHub Pages.

## Vi sao `127.0.0.1:8000` khong chay

Khi mo frontend bang GitHub Pages, trinh duyet dang truy cap mot website public. Neu giao dien goi toi:

```text
http://127.0.0.1:8000
```

thi dia chi nay chi co y nghia tren chinh may dang chay backend local. Neu may do khong co server FastAPI dang mo, browser se bao:

- `ERR_CONNECTION_REFUSED`
- `Failed to fetch`

## Cac huong thay the

### 1. Render

- Phu hop voi backend FastAPI
- De deploy tu GitHub
- Ho tro env vars tren dashboard
- Co the dung free de test/demo

Tai lieu chinh:

- https://render.com/docs/infrastructure-as-code
- https://render.com/docs/configure-environment-variables
- https://render.com/docs/free

Khi nao nen dung:

- Muon co URL public on dinh cho backend
- Muon ket hop voi GitHub Pages cho frontend
- Muon deploy tu repo hien tai

### 2. Koyeb

- Cung la mot lua chon free-friendly cho web service
- Hop voi app FastAPI nho
- Phai dang ky tai khoan de tao service

Tai lieu chinh:

- https://www.koyeb.com/pricing/
- https://www.koyeb.com/docs/

Khi nao nen dung:

- Muon tim option free khac ngoai Render
- Muon co backend URL public ma khong can chay local

### 3. Tunnel tam thoi tu may local

Co the dung:

- `ngrok`
- `cloudflared tunnel`

Muc tieu:

- chay backend local tren may ban
- tao ra mot URL HTTPS public tam thoi
- dan URL do vao o `Backend URL` tren giao dien GitHub Pages

Khi nao nen dung:

- Muon test nhanh
- Chua muon dang ky host
- Chua muon deploy that

Han che:

- URL co the thay doi
- phu hop demo/test ngan han hon la production

### 4. Chay ca frontend va backend local

Huong it rui ro nhat khi debug:

- mo frontend local
- chay backend local
- khong dung GitHub Pages trong giai doan test API

Khi nao nen dung:

- Muon debug tung buoc
- Muon loai bo cac van de host, CORS, mixed content

## Kien nghi cho du an nay

Voi cong xuong agent QC hien tai:

- `Frontend`: GitHub Pages
- `Backend`: Render hoac Koyeb

Neu uu tien:

- de deploy va hop voi `render.yaml`: chon `Render`
- muon them mot lua chon free-friendly: chon `Koyeb`
- muon test nhanh ngay hom nay: chon `tunnel`

## Lua chon nhanh nhat theo tung muc tieu

### Muon chay that qua internet

Chon:

1. Render
2. Koyeb

### Muon test ngay trong ngay

Chon:

1. Chay backend local
2. Dung tunnel de lay URL HTTPS
3. Dan vao `Backend URL`

### Muon debug cho chac

Chon:

1. Chay frontend local
2. Chay backend local
3. Test hoan toan tren cung mot may

## Ghi chu quan trong

- API key phai nam o backend, khong dua len frontend
- `.env` chi dung cho backend local hoac env vars tren host
- GitHub Pages chi host duoc frontend tinh, khong chay duoc Python workflow
