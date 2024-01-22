create database UngThuDa
use UngThuDa

CREATE TABLE TaiKhoan
(
	taikhoan varchar(51) not null,
	matkhau varchar(51) not null
)

CREATE TABLE ThongTinBenhNhan
(
	MaBN CHAR(10) NOT NULL PRIMARY KEY,
	TenBN NVARCHAR(51) NOT NULL,
	NgaySinh DATE NOT NULL,
    GioiTinh CHAR(5) NOT NULL,
	sdt NVARCHAR(20) NOT NULL,
	DiaChi NVARCHAR(51) NOT NULL,
)

CREATE TABLE LichSuKham
(
    MaBN CHAR(10) NOT NULL,
    NgayKham DATE NOT NULL,
    ChanDoan NVARCHAR(31) NOT NULL,
    PhanTram FLOAT NOT NULL,
    GhiChu NVARCHAR(101) NOT NULL,
	 CONSTRAINT fk_LSK_TTBN FOREIGN KEY (MaBN) REFERENCES ThongTinBenhNhan (MaBN)
);

select * from LichSuKham

insert into TaiKhoan values ('abc', '123')