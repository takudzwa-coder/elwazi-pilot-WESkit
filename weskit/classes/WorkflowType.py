import enum


class WorkflowType(enum.Enum):
    SNAKEMAKE = "snakemake"
    NEXTFLOW = "nextflow"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_
