#include <tna.p4>

typedef bit<48> MacAddr_t;

const bit<16> ETHERTYPE_VLAN = 0x8100;

header Ethernet_h {
    MacAddr_t dstAddr;
    MacAddr_t srcAddr;
    bit<16>   etherType;
}


header VLAN_h {
    bit<3>  pcp;  // Prority code point
    bit<1>  dei;  // Drop eligibility indicator
    bit<12> vid;  // VLAN identifier
    bit<16> etherType;
}


struct TestIngressHeaders_t {
    Ethernet_h  ethernet;
    VLAN_h      vlan;
}


struct EmptyMetadata_t { 
    /* empty */
}

struct EmptyHeaders_t { 
    /* empty */
}



parser TestIngressParser(
        packet_in packet,
        out TestIngressHeaders_t hdr,
        out EmptyMetadata_t meta,
        out ingress_intrinsic_metadata_t ig_intr_md)
{
    state start {
        packet.extract(ig_intr_md);
        packet.advance(PORT_METADATA_SIZE);
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition accept;
    }
}


control TestIngressControl(
        inout TestIngressHeaders_t hdr,
        inout EmptyMetadata_t meta,
        in ingress_intrinsic_metadata_t ig_intr_md,
        in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
        inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
        inout ingress_intrinsic_metadata_for_tm_t ig_tm_md)
{
    action forward(PortId_t egress_port) {
        ig_tm_md.ucast_egress_port = egress_port;

        hdr.vlan.setValid();
        hdr.vlan.etherType = hdr.ethernet.etherType;
        hdr.vlan.vid = (bit<12>)ig_intr_md.ingress_port;
        hdr.vlan.dei = 0;
        hdr.vlan.pcp = 0;

        hdr.ethernet.etherType = ETHERTYPE_VLAN;
    }

    action drop() {
        ig_dprsr_md.drop_ctl = 1;
        exit;
    }

    table port_forward_exact {
        key = {
            ig_intr_md.ingress_port: exact;
        }
        actions = {
            drop;
            forward;
        }
        size = 512;
        default_action = drop;
    }

    table port_forward_ternary {
        key = {
            hdr.ethernet.srcAddr: ternary;
        }
        actions = {
            drop;
            forward;
        }
        size = 512;
        default_action = drop;
    }


    table port_forward_lpm {
        key = {
            hdr.ethernet.srcAddr: lpm;
        }
        actions = {
            drop;
            forward;
        }
        size = 512;
        default_action = drop;
    }

    apply { 
        port_forward_exact.apply();
        port_forward_ternary.apply();
        port_forward_lpm.apply();
        ig_tm_md.bypass_egress = 1w1;
    }
}


control TestIngressDeparser(
        packet_out packet,
        inout TestIngressHeaders_t hdr,
        in EmptyMetadata_t meta,
        in ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
        packet.emit(hdr);
    }
}









parser EmptyEgressParser(
        packet_in pkt,
        out EmptyHeaders_t hdr,
        out EmptyMetadata_t eg_md,
        out egress_intrinsic_metadata_t eg_intr_md) {
    state start {
        transition accept;
    }
}

control EmptyEgressControl(
        inout EmptyHeaders_t hdr,
        inout EmptyMetadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {
    apply {}
}

control EmptyEgressDeparser(
        packet_out pkt,
        inout EmptyHeaders_t hdr,
        in EmptyMetadata_t eg_md,
        in egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md) {
    apply {}
}




Pipeline(
    TestIngressParser(),
    TestIngressControl(),
    TestIngressDeparser(),
    EmptyEgressParser(),
    EmptyEgressControl(),
    EmptyEgressDeparser()
) pipe;

Switch(pipe) main;
