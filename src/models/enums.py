"""Enum definitions for NACC asset declaration data."""

from enum import IntEnum


class RelationshipType(IntEnum):
    """Relationship types for relatives."""
    FATHER = 1  # บิดา
    MOTHER = 2  # มารดา
    SIBLING = 3  # พี่น้อง
    CHILD = 4  # บุตร
    SPOUSE_FATHER = 5  # บิดาคู่สมรส
    SPOUSE_MOTHER = 6  # มารดาคู่สมรส


class PositionPeriodType(IntEnum):
    """Position period types."""
    CURRENT = 1  # ตำแหน่งปัจจุบัน
    CONCURRENT = 2  # ตำแหน่งที่ดำรงอยู่พร้อมกัน
    PAST = 3  # ตำแหน่งในอดีต


class PositionCategoryType(IntEnum):
    """Position category types."""
    PM = 1  # นายกรัฐมนตรี
    DEPUTY_PM = 2  # รองนายกรัฐมนตรี
    MINISTER = 3  # รัฐมนตรี
    MP = 4  # ส.ส.
    SENATOR = 5  # ส.ว.
    OTHER = 6  # อื่นๆ


class StatementType(IntEnum):
    """Financial statement types."""
    CASH = 1  # เงินสด
    DEPOSITS = 2  # เงินฝาก
    LOANS = 3  # เงินให้กู้ยืม
    ASSETS = 4  # ทรัพย์สิน
    LIABILITIES = 5  # หนี้สิน


class StatementDetailType(IntEnum):
    """Statement detail types."""
    BANK_ACCOUNT = 1
    CASH = 2
    DEPOSITS = 3
    BONDS = 4
    STOCKS = 5
    LOANS_GIVEN = 6
    OTHER = 7


class DateAcquiringType(IntEnum):
    """Date acquiring type - how precise the date is."""
    EXACT = 1  # ที่แน่นอน
    APPROXIMATE = 2  # โดยประมาณ
    NOT_SPECIFIED = 3  # ไม่ระบุ
    NONE = 4  # ไม่มี


class DateEndingType(IntEnum):
    """Date ending type."""
    EXACT = 1  # ที่แน่นอน
    APPROXIMATE = 2  # โดยประมาณ
    NOT_SPECIFIED = 3  # ไม่ระบุ
    NONE = 4  # ไม่มี


class AssetAcquisitionType(IntEnum):
    """How the asset was acquired."""
    INHERITANCE = 1  # มรดก
    PURCHASE = 2  # ซื้อ
    GIFT = 3  # ได้รับเป็นของขวัญ
    RENT = 4  # เช่า
    BUILT = 5  # ปลูกสร้าง
    NATURAL = 6  # ได้มาตามปกติ
    OTHER = 7  # อื่นๆ


class AssetType(IntEnum):
    """Asset type IDs from enum_type/asset_type.csv."""
    # ที่ดิน (Land)
    LAND_CHANOT = 1  # โฉนด
    LAND_SPK = 2  # ส.ป.ก
    LAND_SPK_4_01 = 3  # ส.ป.ก 4-01
    LAND_NS3 = 4  # น.ส.3
    LAND_NS3K = 5  # น.ส.3ก
    LAND_PBT5 = 6  # ภบท.5
    LAND_CONDO = 7  # ห้องชุด (อ.ช.2)
    LAND_CONTRACT = 8  # สัญญาซื้อขาย
    LAND_NK3 = 9  # น.ค.3

    # โรงเรือนและสิ่งปลูกสร้าง (Buildings)
    BUILDING_HOUSE = 10  # บ้าน
    BUILDING_BUILDING = 11  # อาคาร
    BUILDING_TOWER = 12  # ตึก
    BUILDING_CONDO = 13  # ห้องชุด
    BUILDING_CONDOMINIUM = 14  # คอนโด
    BUILDING_DORMITORY = 15  # หอพัก
    BUILDING_PARKING = 16  # ลานจอดรถ
    BUILDING_FACTORY = 17  # โรงงาน

    # ยานพาหนะ (Vehicles)
    VEHICLE_CAR = 18  # รถยนต์
    VEHICLE_MOTORCYCLE = 19  # จักรยานยนต์
    VEHICLE_BOAT = 20  # เรือยนต์
    VEHICLE_PLANE = 21  # เครื่องบิน

    # สิทธิและสัมปทาน (Rights and Concessions)
    RIGHTS_INSURANCE = 22  # กรมธรรม์
    RIGHTS_CONTRACT = 23  # สัญญา
    RIGHTS_MEMBERSHIP = 24  # สมาชิก
    RIGHTS_FUND = 25  # กองทุน
    RIGHTS_PENSION = 26  # เงินสงเคราะห์
    RIGHTS_AUCTION = 27  # ป้ายประมูล

    # ทรัพย์สินอื่น (Other Assets)
    OTHER_BAG = 28  # กระเป๋า
    OTHER_GUN = 29  # อาวุธปืน
    OTHER_WATCH = 30  # นาฬิกา
    OTHER_JEWELRY = 31  # เครื่องประดับ
    OTHER_AMULET = 32  # วัตถุมงคล
    OTHER_GOLD = 33  # ทองคำ
    OTHER_ART = 34  # งานศิลปะ โบราณวัตถุ
    OTHER_COLLECTION = 35  # ของสะสมอื่น

    # อื่นๆ (Others)
    LAND_OTHER = 36  # ที่ดินอื่นๆ
    BUILDING_OTHER = 37  # สิ่งปลูกสร้างอื่นๆ
    VEHICLE_OTHER = 38  # ยานพาหนะอื่นๆ
    RIGHTS_OTHER = 39  # สิทธิอื่นๆ
